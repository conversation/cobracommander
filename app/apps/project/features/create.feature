Feature: I can create and a new Project
    I should be able to create a new Project
    I should not be able to create a new Project with a name that already exists
    
    Scenario: I can create a new Project
        Given that I am on the build dashboard
        And I click link with text "Add new Project"
        And I fill in "name" field with "ROFLCOPTER Inc."
        And I click button with name "save"
        I should see text "ROFLCOPTER Inc."
    
    Scenario: Create a new Project with a name that already exists
        Given that I am on the build dashboard
        And I click link with text "Add new Project"
        And I fill in "name" field with "WTF Barbecue"
        And I click button with name "save"
        I should see text "A Project with that name already exists"