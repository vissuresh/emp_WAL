## Problem statement

We need a system to be able to manage data for employees. Requests will be accepted over HTTP ([API contract](#api-contract)). No databases/libraries can be used to store/maintain data.

------

### Technical details
1. Your repository needs to have a `Dockerfile` that starts your HTTP web app
2. Your HTTP app need to expose APIs ([API contract](#api-contract)) on port 8080
3. No existing databases, libraries and services can be used to store the data
4. Application needs to persist data across restarts
5. No limitation on the programming language
6. Do not touch the GitHub actions code. It is used to test your code automatically and score it. Any modifications will lead to immediate disqualification.
7. Maximum time a single request can take is 10 seconds
8. Data should be persisted in `/home/`

#### FAQ
1. Do not run a development webserver with watch enabled in your app. Your tests will fail.
2. If your greeting end point test is not passing, please check the output you produce. It needs to be exactly what is requested.
3. When in doubt, please check the Github Actions logs for details
4. Logs for the performance tests will not be shared

## Data to be stored
```
{
    employeeId: string,
    name: string,
    city: string
}
```
---
## API contract
***
>##### GET /greeting
Checks whether the service is available.

###### Response
* Code: 200  
* Content: `Hello world!` 
---

>##### POST /employee
Creates a new Employee and returns the employeeId

###### Request & Response headers
Content-Type: application/json

###### Body
```
{
    name: string,
    city: string
}
```
###### Success Response
* Status code: 201
* Content: `{ "employeeId": "<employee_id>" }` (Note: Employee ID is a `string`)
---

>##### GET /employee/:id
Returns the specified employee.

###### URL Params
`id=[string]` *Required*

###### Success Response
* Status code: 200
* Content: `{ <employee_object> }`

###### Error Response
* Status code: 404
* Content: `{ message : "Employee with <employee_id> was not found" }`
---

>##### GET /employees/all
Returns list of all employees.

###### Success Response
* Status code: 200
* Content: `[{ <employee_object> }]`
---

>##### PUT /employee/:id
Updates fields of the existing employee and returns the new object.

###### URL Params
`id=[string]` *Required*

###### Headers
Content-Type: application/json

###### Body
```
{
    name: string,
    city: string
}
```

###### Success Response
* Code: 201
* Content: `{ <employee_object> }`

###### Error Response
* Code: 404
* Content: `{ message : "Employee with <employee_id> was not found" }`
---

>##### DELETE /employee/:id
  Deletes existing employee record.

###### URL Params
`id=[string]` *Required*

###### Success Response
* Status code: 200
* Content:  `{ <employee_object> }`

###### Error Response
* Status code: 404
* Content: `{ message : "Employee with <employee_id> was not found" }`
---

>##### POST /employees/search
  Search employees with different criteria.

Search by name
###### Headers
Content-Type: application/json

###### Body

```
{
    "fields": [<filter-criterion>],
    "condition": "<AND|OR>" 
}
```

*   `fields` is *required*, and  `filter-criterion` is of the following shape
  ```
  {
      fieldName: string,
      eq: string,
      neq: string
  }
  ```
  
  `fieldName` is *required* and can be either of
  * `name`
  * `city`
  
  Either of `eq` or `neq` needs to be supplied - never both.
  `eq` and `neq` hold string values to check for, respectively, equality or non-equality of the value stored in the requested `fieldName`.

* `condition` is *optional* and its value is *AND* by default. Allowed values are
  * AND
  * OR

Examples:
```json
{
    "fields": [
        {
            "fieldName": "name",
            "eq": "Apple"
        }
    ]
}
```

```json
{
    "fields": [
        {
            "fieldName": "name",
            "eq": "Apple"
        },
        {
            "fieldName": "city",
            "neq": "Mumbai"
        }
    ],
  "condition": "OR"
}
```

###### Success Response
* Status code: 200
* Content: `[{ <employee_object> }]`
---

###### Error Responses
Empty search criteria should produce an error response.

* Empty object in body, or with an empty `fields` array
  * Status code: 400
  * Content: ```{"messages": ["At least one search criteria should be passed."]}```

* Missing `fieldName`
  * Status code: 400
  * Content: ```{"messages": ["fieldName must be set."]}```

* Missing `eq` or `neq`
  * Status code: 400
  * Content: ```{"messages": ["<fieldName>: At least one of eq, neq must be set."]}```

* Multiple values in `fields` with errors
  * Status code: 400
  * Content: ```{"messages": [message1,message2,...]}```
  * Example of the `message` value with two fields, with the first missing the `fieldName` and the second with `fieldName` *name* but missing both `eq` and `neq`
    - ```["fieldName must be set.", "name: At least one of eq, neq must be set."]```

----
[API Sample Request Response](api-sample.md)