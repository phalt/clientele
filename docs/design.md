# 🎨 Design

## A brief history of HTTP APIs

Hello, I am [Paul Hallett](https://paulwrites.software) - a lead software engineer who has spent over 10 years fascinated by and building HTTP APIs for both massive and small tech companies.

When I started building my first hobby project - [PokeAPI](https://pokeapi.co) - I had one issue I wanted to solve: show how important good API design is by building a "pure" example. PokeAPI was a huge success, and still is, with over 1 billion API requests a month, it is one of the most popular free HTTP APIs on the web.

Around this time [Swagger](https://swagger.io/) was being introduced. Slowly over time adoption built up. This was also around the same time the SaaS and "API product" boom happened - companies like Twilio, Stripe, and Sendgrid were the coolest startups in tech and their product was pure HTTP APIs. A lot of them offered Swagger schemas for their APIs.

In 2015 Swagger was renamed to OpenAPI. Two years later the 3.0 version of finalised, with version 3.1 coming along in 2021.

## OpenAPI client generators

Every few years I check the HTTP API landscape to see what has changed, and what new tooling is available.

A big part of this research is seeing how far [OpenAPI client generators](https://www.openapis.org/) have come.  

Despite the heavy adoption of OpenAPI _schema_ generators, the "last mile" (i.e. - generating, and using, a client library) still has a experience nowhere near the maturity as the schema generator landscape. The great thing about schema generators these days is they are seemlessly blended in - most API frameworks, especially in the Python landscape, generate schemas as standard.

But my experience with most _client_ generators always falls into one of these buckets:

* The generated code is difficult to read, meaning I don't fully trust it, and often leads to problems when trying to debug the code. Nearly all of the time the code is not idiomatic to Python.

* The generated code is often repetitive and very large, meaning it is tedious to support.

* You have to install a lot of extra tooling just to get started.

This experience isn't ideal, and is often such an impedance that it just isn't worth it. I would always prefer instead to take a template of my own choosing, refined from years of working with HTTP APIs, and adapt it to whatever new API I was consuming. And this isn't just my own personal opinion - in every place I have worked I have seen this - developers never using a client generator and instead opting to just roll with a custom built client.

Just as the Python community made a great experience for _schema_ generators, surely we could make one for _client_ generators?

## 2023 and the start of Clientele

In the early part of 2023, I had to build an integration with a new HTTP API.

So, like I did in the past, I used it as an opportunity to asses the landscape of OpenAPI client generators.

And this was our summary at the time of writing:

* API tools and providers had adopted OpenAPI very well. For example - tools like [FastAPI](https://fastapi.tiangolo.com/) and [drf-spectacular](https://github.com/tfranzel/drf-spectacular) now make it easy for the most popular python web frameworks to publish OpenAPI schemas.

* There are a lot of options for generating clients. They all meet the need of "generating a python client using the schema". But, almost universally, they have a poor developer experience.

After evaluating many python client generators, I opted to use **none** of them and instead hand craft the API client myself. I used the OpenAPI schema as a source to develop the input and output objects. Then I wrote a small functional abstraction over the paths.

Looking back over my organised, pythonic, minimal client integration, I had an idea:

> If this is the type of client I would like a client generator to produce; how hard could it be to work backwards and generate this layout?

The schema became my input. The client I had just made became my output. I had all the parts I needed to start a project.

This was the start of Clientele.

## Clientele

As a python developer I know what makes good, readable, idiomatic python.

I also feel like I have a pretty good grasp on the best tools to be using in our python projects as I'm involved in the community and constantly trying out new stuff.

By starting with a client library that I like to use, and working backwards, I was able to build a client generator that produced something that I felt that python developers actually wanted.

But why is _this_ the OpenAPI Python client that I think everyone should use?

### Strongly-typed inputs and outputs

OpenAPI prides itself on being able to describe the input and output objects in its schema.

This means you can build strongly-typed interfaces to the API. This helps to solve some common niggles when using an API - such as casting a value to a string when it should be an integer.

With Clientele, I opted to use [Pydantic](https://docs.pydantic.dev/latest/) to build the models from the OpenAPI schema.

Pydantic doesn't only describe the shape of an object, it also validates the attributes. If an API sends back the wrong attributes at runtime, Pydantic will error and provide a detailed description of what went wrong. It's also super fast.

### Idiomatic Python

A lot of the client generators I tested produced a lot of obtuse and hard to read code.

It was clear in a few cases that the client generator was built without understanding or knowledge of good [Python conventions](https://realpython.com/lessons/zen-of-python/). Usually these client generators offered output in hundreds of programming languages, so they didn't dedicate any time to making the developer experience great in any of them.

I also discovered more than one client generator that would work by reading a file at runtime. This is cool engineering, but it is impractical to use. When you develop with these clients, the available functions and objects don't exist until the code is running, and you can't use an IDE's autocomplete feature.

Clientele sets out to be as pythonic as possible. 

It uses modern tools, idiomatic conventions, and provide some helpful bonuses like [Ruff](https://github.com/astral-sh/ruff) auto-formatting.

### Easy to understand

Eventually a developer will need to do some debugging, and sometimes they'll need to do it in the generated client code.

A lot of the other client generators make obscure or obtuse code that is hard to pick apart and debug.

Now, there's a suggestion that developers _shouldn't have to_ look at this, and that's fair. 

But the reality doesn't match that expectation. Personally, I like to know what generated code is doing. I want to trust that it will work, and that I can adapt around it if needed. An interesting quirk of any code generator is you can't always inspect the source when evaluating whether to use it. Any other tool - you'd just go to GitHub and have a read around, but you can't with code generators.

So the code that is generated needs to be easy to understand.

Clientele doesn't do any tricks, or magic, or anything complex. The generated code has documentation and is designed to be readable. It is only a small layer on top of already well established tools, such as [HTTPX](https://github.com/encode/httpx).

In fact, I have some generated clients in our [project repository](https://github.com/phalt/clientele/tree/main/tests) so you can see what it looks like. We even have example [tests](https://github.com/phalt/clientele/blob/main/tests/test_generated_client.py) for you to learn how to integrate with it.

It is that way because I know you will need to inspect it in the future. I want you to know that this is a sane and sensible tool.

### Supporting Python API Frameworks

The python ecosystem for API frameworks is very rich and mature. I love the options we have to build APIs with. I wanted to focus on supporting this ecosystem specifically because of how much I love the tooling, but also because it means I can focus on doing one thing great: client generation that specifically supports Python API frameworks.

You'll see in the project documentation that we explain how to use common API frameworks like FastAPI, Django REST Framework and Django-ninja, and the project even has [client and server examples](https://github.com/phalt/clientele/tree/main/server_examples) to help demonstrate and prove it's usefulness.
