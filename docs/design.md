# 🎨 Design

## OpenAPI code generators

Every few years we check the HTTP API landscape to see what has changed, and what new tooling is available. A part of this research is seeing how far [OpenAPI client generators](https://www.openapis.org/) have come.  

In the early years of OpenAPI, the "last mile" (i.e. - generating, and using, a client library) had a pretty poor experience:

* The generated code was difficult to read, leading to problems when debugging the code. It was often not idiomatic to the language.

* It was often bloated and repetitive, making changes tedious to support your specific project.

* Also, you had to install a lot of things like Java to generate the code.

* And finally, some API services still weren't publishing an OpenAPI schema. Or, the schema they published was different from the standard, so would not work with code generators.

This experience wasn't ideal, and was often such an impedance that it put us off using them. We would prefer instead to take a template of our own choosing, refined from years of working with HTTP APIs, and adapt it to whatever new API we were consuming.

## The landscape in 2023

In the early part of 2023, we had to build an integration with a new HTTP API. So, like we did in the past, we used it as an opportunity to asses the landscape of OpenAPI client generators.

And this was our summary at the time of writing:

* API tools and providers had adopted OpenAPI very well. For example - tools like [FastAPI](https://fastapi.tiangolo.com/) and [drf-spectacular](https://github.com/tfranzel/drf-spectacular) now make it easy for the most popular python web frameworks to publish OpenAPI schemas.

* There are a lot of options for generating clients. They all meet the need of "generating a python client using the schema". But, almost universally, they have a poor developer experience.

After evaluating many python client generators, we opted to use **none** of them and hand craft the API client ourselves. We used the OpenAPI schema as a source to develop the input and output objects.  Then we wrote a small functional abstraction over the paths.

Looking back over our organised, pythonic, minimal client integration, we had an idea:

If this is the type of client we would like a generator to produce; how hard could it be to work backwards and build one?

This was the start of Clientele.

## Clientele

As python developers ourselves, we know what makes good, readable, idiomatic python.

We also feel like we have a grasp on the best tools to be using in our python projects.

By starting with a client library that we _like_ to use, and working backwards, we were able to build a client generator that produced something that python developers actually wanted.

But what is it exactly that we aimed to do with Clientele, why is this the OpenAPI Python client that you should use?

### Strongly-typed inputs and outputs

OpenAPI prides itself on being able to describe the input and output objects in it's schema.

This means you can build strongly-typed interfaces to the API. This helps to solve some common niggles when using an API - such as casting a value to a string when it should be an integer.

With Clientele, we opted to use [Pydantic](https://docs.pydantic.dev/latest/) to build the models from the OpenAPI schema.

Pydantic doesn't only describe the shape of an object, it also validates the attributes as well. If an API sends back the wrong attributes at run time, Pydantic will error and provide a detail description about what went wrong.

### Idiomatic Python

A lot of the client generators we tested produced a lot of poor code.

It was clear in a few cases that the client generator was built without understanding or knowledge of good [python conventions](https://realpython.com/lessons/zen-of-python/).

In more than one case we also discovered the client generator would work by reading a file at run time. This is a very cool piece of engineering, but it is impractical to use. When you develop with these clients, the available functions and objects don't exist and you can't use an IDE's auto-complete feature.

Clientele set out to be as pythonic as possible. We use modern tools,  idiomatic conventions, and provide some helpful bonuses like [Black](https://github.com/psf/black/) auto-formatting.

### Easy to understand

Eventually a developer will need to do some debugging, and sometimes they'll need to do it in the generated client code.

A lot of the other client generators make obscure or obtuse code that is hard to pick apart and debug.

Now, there is a suggestion that developers shouldn't _have to_ look at this, and that is fair. But the reality doesn't match that expectation. Personally; we like to know what generated code is doing. We want to trust that it will work, and that we can adapt around it if needs be. An interesting quirk of any code generator is you can't always inspect the source when evaluating to use it. Any other tool - you'd just go to GitHub and have a read around, but you can't with code generators.

So the code that is generated needs to be easy to understand.

Clientele doesn't do any tricks, or magic, or anything complex. The generated code has documentation and is designed to be readable. It is only a small layer on top of already well established tools, such as [HTTPX](https://github.com/encode/httpx).

In fact, we have some generated clients in our [project repository](https://github.com/phalt/clientele/tree/main/tests) so you can see what it looks like. We even have example [tests](https://github.com/phalt/clientele/blob/main/tests/test_generated_client.py) for you to learn how to integrate with it.

It is that way because we know you will need to inspect it in the future. We want you to know that this is a sane and sensible tool.
