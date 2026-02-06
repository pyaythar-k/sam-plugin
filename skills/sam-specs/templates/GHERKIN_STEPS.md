# Gherkin Steps Library

Reusable Gherkin steps for common test patterns. This library provides standardized step definitions that can be used across user stories to ensure consistency and reduce test maintenance.

---

## Authentication Steps

### Given Steps

**Given** I am logged in as an `<user_role>`
**Given** I am not logged in
**Given** my account is `<account_status>`
**Given** I have an expired authentication token

### When Steps

**When** I log in with email `<email>` and password `<password>`
**When** I log out
**When** I refresh my authentication token
**When** I request a password reset for `<email>`

### Then Steps

**Then** I should be authenticated
**Then** I should receive an authentication token
**Then** I should receive a `<status_code>` status code
**Then** I should see an authentication error message

---

## Data Management Steps

### Given Steps

**Given** the database is empty
**Given** there are `<count>` `<resource_type>` in the database
**Given** a `<resource_type>` with `<attribute>` of `<value>` exists
**Given** the following `<resource_type>` exist:
| id | name | status |
| 1 | Test 1 | active |
| 2 | Test 2 | inactive |

### When Steps

**When** I create a `<resource_type>` with:
| field | value |
| name | Test Name |
| status | active |

**When** I update the `<resource_type>` with id `<id>`
**When** I delete the `<resource_type>` with id `<id>`
**When** I request all `<resource_type>`
**When** I request the `<resource_type>` with id `<id>`

### Then Steps

**Then** the `<resource_type>` should be created
**Then** the `<resource_type>` should be updated
**Then** the `<resource_type>` should be deleted
**Then** I should receive `<count>` `<resource_type>`
**Then** the `<attribute>` should be `<value>`
**Then** the response should contain:
| field | value |
| id | 123 |
| name | Test Name |

---

## API Interaction Steps

### Given Steps

**Given** the API server is running
**Given** the API endpoint `<endpoint>` is available
**Given** I have valid API credentials

### When Steps

**When** I send a `<method>` request to `<endpoint>`
**When** I send a `<method>` request to `<endpoint>` with:
| header | value |
| Authorization | Bearer <token> |
| Content-Type | application/json |

**When** I send a `<method>` request to `<endpoint>` with body:
| field | value |
| name | Test |
| email | test@example.com |

### Then Steps

**Then** I should receive a `<status_code>` status code
**Then** the response should be valid JSON
**Then** the response should contain field `<field_name>`
**Then** the response field `<field_name>` should equal `<value>`
**Then** the response should match schema:
```json
{
  "type": "object",
  "required": ["id", "name"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"}
  }
}
```

---

## UI Interaction Steps

### Given Steps

**Given** I am on the `<page_name>` page
**Given** the `<element_name>` element is visible
**Given** the `<element_name>` element is disabled
**Given** I have filled in `<field_name>` with `<value>`

### When Steps

**When** I click on the `<element_name>` element
**When** I type `<value>` into the `<field_name>` field
**When** I select `<option>` from the `<dropdown_name>` dropdown
**When** I submit the `<form_name>` form
**When** I navigate to `<url>`

### Then Steps

**Then** I should see the `<element_name>` element
**Then** the `<element_name>` element should contain `<text>`
**Then** the `<element_name>` element should be visible
**Then** the `<element_name>` element should be disabled
**Then** I should be on the `<page_name>` page
**Then** I should see a success message
**Then** I should see an error message containing `<error_text>`

---

## State Management Steps

### Given Steps

**Given** the feature flag `<flag_name>` is enabled
**Given** the application state is:
| state_key | state_value |
| user.authenticated | true |
| user.role | admin |

**Given** the cache is empty
**Given** the `<service_name>` service is available

### When Steps

**When** the state `<state_key>` changes to `<value>`
**When** the cache expires
**When** the `<service_name>` service becomes unavailable

### Then Steps

**Then** the state `<state_key>` should be `<value>`
**Then** the component should re-render
**Then** the cache should contain key `<cache_key>`
**Then** I should see a fallback UI

---

## Async/Promise Steps

### Given Steps

**Given** the async operation is pending
**Given** the request timeout is set to `<timeout>` milliseconds

### When Steps

**When** I wait for the async operation to complete
**When** I wait `<milliseconds>` milliseconds
**When** the request times out

### Then Steps

**Then** the async operation should complete within `<timeout>` milliseconds
**Then** I should see a loading indicator
**Then** I should see a retry button

---

## Error Handling Steps

### Given Steps

**Given** the network is disconnected
**Given** the server returns an error response

### When Steps

**When** an error occurs
**When** I retry the failed request

### Then Steps

**Then** I should see an error message
**Then** the error message should contain `<error_text>`
**Then** I should be able to retry the operation
**Then** the error should be logged

---

## File Upload Steps

### Given Steps

**Given** I have a file named `<filename>` of type `<content_type>`
**Given** the file size is `<size>` bytes

### When Steps

**When** I upload the file `<filename>`
**When** I upload multiple files

### Then Steps

**Then** the file should be uploaded successfully
**Then** I should see a progress bar
**Then** the file should appear in the file list
**Then** the upload should fail if the file size exceeds `<max_size>`

---

## Pagination Steps

### Given Steps

**Given** there are `<total_items>` `<resource_type>` in the database

### When Steps

**When** I request page `<page_number>` with `<page_size>` items per page

### Then Steps

**Then** I should receive `<page_size>` `<resource_type>`
**Then** the total count should be `<total_items>`
**Then** the current page should be `<page_number>`
**Then** there should be a next page link
**Then** there should be a previous page link

---

## Search and Filter Steps

### Given Steps

**Given** there are `<resource_type>` with various attributes

### When Steps

**When** I search for `<search_term>`
**When** I filter by `<filter_field>` with value `<filter_value>`
**When** I sort by `<sort_field>` in `<sort_order>` order

### Then Steps

**Then** I should see results matching `<search_term>`
**Then** all results should have `<filter_field>` equal to `<filter_value>`
**Then** results should be sorted by `<sort_field>` in `<sort_order>` order
**Then** I should see `<count>` results

---

## Notification Steps

### Given Steps

**Given** I have enabled notifications for `<notification_type>`

### When Steps

**When** a `<event_type>` event occurs
**When** I dismiss the notification

### Then Steps

**Then** I should receive a notification
**Then** the notification should contain `<message>`
**Then** the notification should have type `<notification_type>`
**Then** the notification should auto-dismiss after `<seconds>` seconds

---

## Usage Examples

### Example 1: User Authentication Scenario

```gherkin
Scenario: User logs in with valid credentials
  Given I am on the login page
  When I type "user@example.com" into the email field
  And I type "password123" into the password field
  And I click on the login button
  Then I should be authenticated
  And I should be on the dashboard page
  And I should see a welcome message
```

### Example 2: API Resource Creation with Scenario Outline

```gherkin
Scenario Outline: Create resource with different validation states
  Given I am logged in as an admin
  When I send a POST request to /api/resources with body:
    | field | value |
    | name | <name> |
    | type | <type> |
  Then I should receive a <status_code> status code

  Examples:
    | name | type | status_code |
    | Valid Resource | standard | 201 |
    | | premium | 400 |
    | Duplicate | standard | 409 |
```

### Example 3: Async Operation with Error Handling

```gherkin
Scenario: Handle failed async operation
  Given the server is unavailable
  When I request the user profile
  Then I should see an error message containing "Failed to load"
  And I should see a retry button
  When I click on the retry button
  And the server becomes available
  Then I should see the user profile
```

---

## Best Practices

1. **Use business language, not technical implementation**
   - ✅ "When I submit the form"
   - ❌ "When I POST to /api/users"

2. **Keep steps focused and reusable**
   - ✅ "When I log in with valid credentials"
   - ❌ "When I click the login button, type my email, type my password, and click submit"

3. **Use scenario outlines for data-driven tests**
   - Reduces duplication
   - Makes test coverage explicit

4. **Parameterize values, not behavior**
   - ✅ "When I create a user with `<role>`"
   - ❌ "When I create an admin user" + "When I create a guest user"

5. **Organize scenarios by user story acceptance criteria**
   - One AC may map to multiple scenarios
   - Ensure all ACs have corresponding test scenarios
