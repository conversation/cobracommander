# A rough TODO for Cobra Commander

This is pretty high level architecture wankinness really — I just want to get some ideas down about how I think we should try and approach the problem.

## We use Jenkins. We don’t like it. Why?

So Jenkins does most of the things we want right? But it does a bunch of things rather terribly. Most of which — it seems to me — are as a result of it being way over engineered for what we need, right?

What we really want is something with the simplicity of CI-Joe, but maybe slightly more featured and a tonne more polished? The features that jump out to me;

- ability to build > 1 project/codebase
- better control over what is being tested (ie: build this branch, etc)
- better alerting when the build is in a failing state
- generic trend reporting on the codebase (ie: coverage reports)

