from flask import Flask, render_template, request, jsonify
from config import DevelopmentConfig, ProductionConfig
import os
import os.path
import re
import subprocess

app = Flask(__name__)

if os.environ.get('ENV_MODE') == 'prod':
    app.config.from_object('app.ProductionConfig')
else:
    app.config.from_object('app.DevelopmentConfig')

@app.before_request
def hook():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401

    if token != f"Bearer {app.config['ACCESS_TOKEN']}":
        return jsonify({'message': 'Invalid token!'}), 401


@app.route('/zone/new', methods=['POST'])
def new_zone():
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            raise ValueError("The field 'name' is required.")
        retry = validate_int_field(data.get('retry'), 'retry')
        expire = validate_int_field(data.get('expire'), 'expire')
        refresh = validate_int_field(data.get('refresh'), 'refresh')
        minimum = validate_int_field(data.get('minimum'), 'minimum')
        ttl = validate_int_field(data.get('ttl'), 'ttl')
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

#     ip = data.get('ipv4')
#     ipv4_pattern = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
#     if(not ipv4_pattern.match(ip)){
#         return jsonify({'message': 'Ipv4 invalid'}), 403
#     }

    if zone_file_exists(name):
        return jsonify({'message': 'Zone already defined'}), 409
    else:
        configFile = open(DevelopmentConfig.CONFIG_ZONE_PATH, "a")
        configFile.write(render_template('tpl/zone/config.txt', name= name))
        configFile.close()

        fichier = open(get_zone_filename(name), "w")
        fichier.write(render_template('tpl/zone/records.txt', name= name, nsName= app.config['ZONE_BASE_IP'],minimum=minimum, retry=retry, refresh= refresh, ttl= ttl, expire= expire ))
        fichier.close()

    try:
        result = subprocess.run(["rndc", "reconfig"], capture_output=True, text=True, check=True)
        return jsonify({'message': 'Zone created', 'code': result.returncode}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Script execution "rndc reconfig" failed', 'message': str(e)}), 500


@app.route('/zone/can-add', methods=['POST'])
def can_add_zone():
    data = request.get_json()
    name = data.get('name')
    if zone_file_exists(name):
        return jsonify({'message': 'Zone already defined'}), 409

    return jsonify({'message': 'Zone can be created'}), 200

@app.route('/zone/<zone_name>', methods=['DELETE'])
def remove_zone(zone_name):
    remove_zone_from_file(app.config['CONFIG_ZONE_PATH'], zone_name)
    os.remove(get_zone_filename(zone_name))

    try:
        result = subprocess.run(["rndc", "reload"], capture_output=True, text=True, check=True)
        return jsonify({"message": f"Zone '{zone_name}' successfully deleted."}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Script execution "rndc reconfig" failed', 'message': str(e)}), 500


@app.route('/zone/<zone_name>/file', methods=['GET'])
def get_file_content(zone_name):
    if zone_file_exists(zone_name):
        with open(get_zone_filename(zone_name), 'r') as file:
            return file.read(), 200
    return jsonify({'message': 'File not found'}), 404

@app.route('/zone/search', methods=['GET'])
def search_zones():
    search = request.args.get('query')
    matching_zones = search_zones_in_file(app.config['CONFIG_ZONE_PATH'], search)
    return jsonify(matching_zones)

def remove_zone_from_file(file_path, zone_name):
    with open(file_path, 'r') as file:
        config_content = file.read()
    zone_pattern = re.compile(r'zone\s+"{}"[\s\S]*?;\n}};\n'.format(re.escape(zone_name)), re.MULTILINE)
    new_config_content = zone_pattern.sub('', config_content)
    with open(file_path, 'w') as file:
        file.write(new_config_content)

def zone_file_exists(name):
    configFile = open(app.config['CONFIG_ZONE_PATH'], "r")
    zoneAlreadyConfigure = configFile.read().find('zone "'+ name +'"') != -1
    configFile.close()
    return zoneAlreadyConfigure or os.path.exists(get_zone_filename(name))

def get_zone_filename(name):
    return app.config['ZONE_PATH'] + name + '.db'

def validate_int_field(value, field_name):
    if value is None:
        raise ValueError(f"The field '{field_name}' is required and cannot be null.")
    if not isinstance(value, int):
        raise ValueError(f"The field '{field_name}' must be an integer.")
    return value

def search_zones_in_file(file_path, search_term):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            pattern = fr'zone\s+"([^"]*{re.escape(search_term)}[^"]*)"'
            matching_zones = re.findall(pattern, content, re.IGNORECASE)
            return matching_zones
    except FileNotFoundError:
        print(f"Fichier non trouvé: {file_path}")
        return []