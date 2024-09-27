ifndef VERBOSE
.SILENT:
endif

COLOR_TITLE = \033[33m
COLOR_RESET = \033[0m

DOCKER_COMPOSE = cd .docker && docker-compose

define echo-title
  printf "\n$(COLOR_TITLE)****************************************************************\n"
  printf "*$(1)\n"
  printf "$(COLOR_TITLE)****************************************************************$(COLOR_RESET)\n\n"
endef


docker-compose-build:
	$(DOCKER_COMPOSE) build --pull

##
## Project
## -------
##

project-install: acl dev-stop docker-compose-build dns-fixtures dev-start ## Install the project and start the dev environment

dev-start: ## Start the dev environment
	$(call echo-title, Starting docker)
	$(DOCKER_COMPOSE) up -d

dev-stop: ## Stop the dev environment
	$(call echo-title, Stopping docker)
	$(DOCKER_COMPOSE) down

dns-fixtures: ## Load DNS fixtures
	cp features/bind/zones/* .docker/var/dns/bind/

dns-logs: ## Show DNS logs
	docker logs -f dns_bind

acl:
	chmod -R 777 .docker/var

.DEFAULT_GOAL := help
help:
	@grep -Eh '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'
