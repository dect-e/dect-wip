# dect-wip
`Webinterface for usercreation und selfregistration with interfaces for external phonebooks, Asterisk-provisioning and OMM-synchronisation.`

## Our Usecase
We want to provide self service telephony on a event. A Webpage for account creation. And self-service number assignment. This means we got SIP and optional DECT infrastructure.

We decided to opensource it as an easy-to-setup software after some requests.

## Software Architecture
- dect-wip core
    - The dect-wip core consists of a sqlite3 database as source of trouth that contains data like users and extensions
    - It also contains the user frontend, delivered by a flask webserver.
    - The core provides a REST API that optional microservices can connect to.
    - dect-wip core is usable offline and does not depend on external resources like databases
- dect-wip services:
    - dect-wip-ommsync checks for newly paired handsets and creates temporary voip accounts for calling the self-registration code.
    - dect-wip-mitel-phonebook provides an endpoint for mitel dect handsets to lookup phonebook entries 

## how to contribute
- This is a fun-project! We don't get paid for this and we might have higher response times
- Fetch a unassigned issue, ask if you don't know anything or are unsure
- don't be disappointed if we don't merge a change/feature. We try to be reasonable but some changes do not fit or are better kept in a separate repository
- create simple logic/codes - we don't have a enterprise project with many experienced developers
- this repository shall not contain install scripts, put platform-specific code in their own repos
- use conventional commits - see below
- we use Semantic Versioning
- don't push to main! do pull-requests
- join our Matrix [#DECT-WIP:matrix.binary-kitchen.de](https://matrix.to/#/%23DECT-WIP%3Amatrix.binary-kitchen.de)

### Our conventinal commits `structual elements` - https://www.conventionalcommits.org/
- feat
- fix
- build
- chore
- ci
- docs
- style
- refactor
- perf
- test

## Maintainer
- @vschlegel
- @TilCreator
- @blackdotraven
