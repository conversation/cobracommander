Feature: I can create and a new Project
    I should be able to create a new Project from a github url
    I should not be able to create a new Project with a name that already exists
    
    Scenario: I can create a new Project using a git url
        Given that I am on the build dashboard
        And I click link with text "Add new Project"
        And I fill in "url" field with "git://github.com/conversation/cobracommander.git"
        And I click button with name "save"
        I should see text "..."
    
    Scenario: I can create a new Project using a http url
        Given that I am on the build dashboard
        And I click link with text "Add new Project"
        And I fill in "url" field with "https://github.com/conversation/cobracommander"
        And I click button with name "save"
        I should see text "..."
    
    Scenario: Create a new Project with a name that already exists
        Given that a project for url "git://github.com/conversation/cobracommander.git" exists
        Given that I am on the build dashboard
        And I click link with text "Add new Project"
        And I fill in "name" field with "git://github.com/conversation/cobracommander.git"
        And I click button with name "save"
        I should see text "A Project with that name already exists"