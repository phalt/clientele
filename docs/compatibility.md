# 💱 Compatability

When we were building Clientele, we discovered that, despite a fantastic [specification](https://www.openapis.org/), OpenAPI has a lot of poor implementations.

As pythonistas, we started with the auto-generated OpenAPI schemas provided by [FastAPI](https://fastapi.tiangolo.com/), and then we branched out to large APIs like [Twilio](https://www.twilio.com/docs/openapi) to test what we built.

Despite the effort, we still keep finding subtly different OpenAPI implementations. Because of this we cannot guarentee 100% compatability with an API, but we can give you a good indication of what we've tested.

## Works well with

Any bog-standard `3.0.x` implementation works very well.

* [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/?h=openapi#what-is-openapi-for)'s OpenAPI schema is very well supported.
* [Microsoft's OpenAPI spec](https://learn.microsoft.com/en-us/azure/api-management/import-api-from-oas?tabs=portal) has also been battle tested on an internal project, and works well.


## Does not work

We do not support `2.x` aka "Swagger" - this format is quite different and deprecated.
