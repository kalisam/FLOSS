    Write a specification.
    Get it reviewed.
    Then write a test plan based on the specification.
    Get it reviewed.
    Then write the tests, based on the test plan.
    Get them reviewed.
    Correct the specification based on the errors this throws up.
    Write the documentation.
    Get it reviewed.
    Correct the specification and test plan based on the errors this throws up.
    Oh, yes. Implement the software. (Nearly forgot.)
    Correct the specification and test plan based on the errors the throws up.
    Run the test suite for each module and for the complete program.
    Fix any bugs and get the changes reviewed before committing them back to the repository.
    This should not be the longest part of the development process (but, sadly, for most people it is).

    One of the biggest thing about programming is being able to break a problem down into chunks and then break those subproblems down. Keep doing that until you get a picture of what specifically you need to do to accomplish each major step. So, if your program needs to do things in three big steps, start even lower than pseudocode; start with a list.

 

use activity diagrams, with arrows.


 Comments should explain why something is to be done, not what is being done.

Maintaining comments is not a second job, it is the FIRST job.

You should always write the comments before you write any code at all. 

Descriptive variable names, descriptive class names, descriptive structure names, descriptive constants etc. etc. are essential for readable and maintainable in the future source code.. 

Descriptive comments and structured programming techniques are probably the best things that all programmers can do at all times

If you notice yourself trying to do too much in a single function, break it down into helper functions, and have your function just call those helper functions. Give the helper functions descriptive names, such that when you read the main function, you know exactly what is happening, without looking at the implementation of the helper functions. 