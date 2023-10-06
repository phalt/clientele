# 🎨 Design

## OpenAPI code generators

Every few years we check the HTTP API landscape to see what has changed, and what tooling is available to use now.

A part of this research is seeing how far [OpenAPI code generators](https://www.openapis.org/) have come.  In the early years of OpenAPI, the "last mile" (i.e. - generating, and using, a client library) had an awful experience:

* The generated code was difficult to read, leading to problems when debugging the code. It was often not idiomatic to the language.

* It was often bloated and repetitive, making changes tedious to support your specific project.

* Also, you had to install a lot of things like Java to generate the code.

* And finally, some API services still weren't publishing an OpenAPI schema. Or, the schema they published was different from the standard, so would not work with code generators.

This experience wasn't ideal, and was often such an impedance that it put us off using them. We would prefer instead to take a template of our own choosing, refined from years of working with HTTP APIs, and adapt it to whatever new API we were consuming.

## The landscape in 2023

In the early part of 2023, we had to build a new integration with a new HTTP API. So, like we did in the past, we used it as an opportunity to asses the landscape again.

And this was our summary of the landscape:

* API tools and providers had adopted OpenAPI very well. Tools like [FastAPI](https://fastapi.tiangolo.com/) and [drf-spectacular](https://github.com/tfranzel/drf-spectacular) now make it easy for the most popular python web frameworks to publish OpenAPI schemas.

* There are a lot of options for generating clients. They all meet the need of "generating a python client using the schema". But, they all have a poor developer experience.

After evaluation many python code generators, we opted to use none of them and hand craft the API client ourselves. We used the OpenAPI schema as a source to develop the input and output objects.  Then we wrote a small functional abstraction over the paths.

Looking back over our organised, pythonic, minimal client integration, we had an idea. If we want a code generator to produce something like this; how hard could it be craft a code generator to product it?

This, was the start of Clientele.

## Clientele

As python developers ourselves, we know what makes good, readable, idiomatic python.

We also feel like we have a grasp on the best tools to be using in our python projects.

By starting with a client library that we _like_ to use, and working backwards, we were able to build a code generator that produced something that python developers actually wanted.
