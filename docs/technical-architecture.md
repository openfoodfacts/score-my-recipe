# Architecture notes

The project first step aims at computing Green Score for recipe but, in the future, itI may also add more scores (Nutri-Score, Nova, etc.).

## A frontend and an API

We want to provide a frontend for the general public to use the tool.
But we also want to provide an API so that re-users might integrate score computations to their own tool.
As we want a wide adoption, we really want the API to contain every bit needed to make their integration easy (whatever the technology they use).

This means **Any business logic must go to the API**.
That is any logic around recipe parsing, ingredients handling, completion, warnings, etc. and of course the score computation.
The frontend should only care about presentation and interaction logic.

## Some best practices

Of course we follow FastAPI and Svelte best practice in general.

Always use pydantic objects to specify the API logic especially return methods.
We should be able to generate a good OpenAPI specification and documentation from it,
and use it to auto-generate the JS wrapper
(potential integrator will also benefit from this OpenAPI).

Try to keep the svelte file small and dealing with one main argument.
- Don't hesitate to create small svelte components 
- Split logic in lib/ (types / ui / api)
