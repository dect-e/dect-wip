# Microservices and API-Endpoints

## dect-wip

### Desciption of Service

WebUI and Core-API-Services.
Expose to Public

### Endpoints

Listen-Port: 8080

`/`

Redirects to `/phonebook/`

`/login/`

[GET] - Returns Login-Page
[POST] - checks Login and procceds in Login-Flow


`/logout`

logout the user / destroies the session

`/phonebook/`

returns HTML-Phonebook for User

`/myextensions/`

[POST] - add extenstion
[DELETE] - delete extenstion
[GET] - show WebUI

`/api/v1/GetUserExtensionByToken/<token>`

return extenstion by Token as json

`/api/v1/GetTempExtensionByCallerid/<callerid>`

return extenstion by Callerid as json

`/api/v1/AddTempExtensionToDB`

add tempextenstion to database

`/api/v1/phonebook`

get all extenstions and names as json


## mitel phonebook

### Description of Service

Create Mitel-Phonebook for OMM (xsi Personal)

### Endpoints

Listen-Port: 8082

`/com.broadsoft.xsi-actions/v2.0/user/<caller>/directories/personal`

Endpoint for OMM to fetch phonebook-Data

## ommsync

### Description of Service

Manages OMM-relatet Taks

### Endpoints

Listen-Port: 8081

`/connect/`

Connect the User to his real Extenstion.
Change TMP-Credentials to User-Credentials in OMM.
Uses Token to find User-Extenstion.

`/trigger/`

Create TMP-Extenstions for all Unbound Dect-Handsets in OMM
