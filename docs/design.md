# 🎨 Design

## OpenAPI code generators

Every few years we check the HTTP API landscape to see what has changed, and what tooling is available to use now.

A part of this research is seeing how far OpenAPI code generators have come.  In the early years of OpenAPI, the "last mile" (i.e. - generating, and using, a client library) had an awful experience:

The generated code was difficult to read, leading to problems when debugging the code. It was often not idiomatic to the language.

It was often bloated and repetitive, making changes tedious to support your specific project.

Also, you had to install a lot of things like Java to generate the code.

And finally, some API services still weren't publishing an OpenAPI schema. Or, the schema they published was different from the standard, so would not work with code generators.

This experience wasn't ideal, and was often such an impedance that it put us off using them. We would prefer instead to take a template of our own choosing, refined from years of working with HTTP APIs, and adapt it to whatever new API we were consuming.

## The landscape in 2023

In the early part of 2023, we had to build a new integration with a new HTTP API. So, like we did in the past, we used it as an opportunity to asses the landscape again.

And this was our summary of the landscape:

* API tools and providers had adopted OpenAPI very well. Tools like FastAPI and drf-spectacular now make it easy for the most popular python web frameworks to publish OpenAPI schemas.

* There are a lot of options for generating clients. They all meet the need of "generating a python client using the schema". But, they all have a poor developer experience.

## Clientele

As python developers ourselves, we know what makes good, readable, idiomatic python.
