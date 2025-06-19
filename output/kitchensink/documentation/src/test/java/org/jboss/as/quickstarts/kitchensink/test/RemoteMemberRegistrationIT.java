/*
 * JBoss, Home of Professional Open Source
 * Copyright 2015, Red Hat, Inc. and/or its affiliates, and individual
 * contributors by the @authors tag. See the copyright.txt in the
 * distribution for a full listing of individual contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.jboss.as.quickstarts.kitchensink.test;

import jakarta.json.Json;
import jakarta.json.JsonObject;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.json.JSONObject;
import org.junit.Assert;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.math.BigInteger;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.logging.Logger;

/**
 * The RemoteMemberRegistrationIT class is responsible for testing the remote member registration functionality
 * of the application. It performs integration tests to ensure that members can be registered and cleaned up
 * correctly through the HTTP API.
 *
 * This class uses the JUnit 5 testing framework and follows the Arrange-Act-Assert pattern for structuring tests.
 * It also utilizes the HttpClient for making HTTP requests to the server.
 *
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023-10-01
 *
 * Related Classes:
 * - Member: Represents a member in the application.
 *
 * Usage Example:
 * To run the tests, use a JUnit-compatible test runner. Ensure that the server is running and accessible.
 *
 * Thread Safety:
 * This class is not thread-safe as it maintains state in the createdId field which is modified during tests.
 */
public class RemoteMemberRegistrationIT {

    // Logger instance for logging test activities
    private static final Logger log = Logger.getLogger(RemoteMemberRegistrationIT.class.getName());

    // Field to store the ID of the created member for cleanup purposes
    private BigInteger createdId;

    /**
     * Retrieves the HTTP endpoint URI for member registration.
     *
     * This method constructs the URI based on the server host environment variable or system property.
     * If neither is set, it defaults to "http://localhost:8080".
     *
     * @return URI for the member registration endpoint.
     * @throws RuntimeException if the URI syntax is incorrect.
     */
    protected URI getHTTPEndpoint() {
        // Retrieve the server host from the environment or system property
        String host = getServerHost();
        
        // Default to localhost if no host is specified
        if (host == null) {
            host = "http://localhost:8080";
        }
        
        // Attempt to create a URI from the host and endpoint path
        try {
            return new URI(host + "/api/members");
        } catch (URISyntaxException ex) {
            // Throw a runtime exception if URI creation fails
            throw new RuntimeException(ex);
        }
    }

    /**
     * Retrieves the server host from the environment variable or system property.
     *
     * @return The server host as a String, or null if not set.
     */
    private String getServerHost() {
        // Check for the SERVER_HOST environment variable
        String host = System.getenv("SERVER_HOST");
        
        // Fallback to the system property if the environment variable is not set
        if (host == null) {
            host = System.getProperty("server.host");
        }
        
        // Return the resolved host
        return host;
    }

    /**
     * Tests the registration of a new member.
     *
     * This method creates a new Member object, sends a POST request to register the member,
     * and asserts that the response status code is 201 (Created). It also logs the created member's ID.
     *
     * @throws Exception if an error occurs during the HTTP request or response handling.
     */
    @Test
    public void testRegister() throws Exception {
        // Create a new Member object to be registered
        Member newMember = new Member();
        newMember.setName("Jane Doe"); // Set the name of the member
        newMember.setEmail("jane@mailinator.com"); // Set the email of the member
        newMember.setPhoneNumber("2125551234"); // Set the phone number of the member
        
        // Build a JSON object representing the new member
        JsonObject json = Json.createObjectBuilder()
                .add("name", "Jane Doe") // Add name to JSON
                .add("email", "jane@mailinator.com") // Add email to JSON
                .add("phoneNumber", "2125551234") // Add phone number to JSON
                .build(); // Build the JSON object
        
        // Create an HTTP POST request to the member registration endpoint
        HttpRequest request = HttpRequest.newBuilder(getHTTPEndpoint())
                .header("Content-Type", "application/json") // Set the content type to JSON
                .POST(HttpRequest.BodyPublishers.ofString(json.toString())) // Set the request body
                .build(); // Build the request
        
        // Send the request and receive the response
        HttpResponse<String> response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
        
        // Assert that the response status code is 201 (Created)
        Assert.assertEquals(201, response.statusCode());
        
        // Parse the response body as a JSON object
        JSONObject jsonObject = new JSONObject(response.body().toString());
        
        // Log the created member's information
        log.info("Member was created: " + jsonObject);
        
        // Store the created member's ID for cleanup
        createdId = new BigInteger(jsonObject.getString("id"));
    }

    /**
     * Cleans up the created member after each test.
     *
     * This method sends a DELETE request to remove the member that was created during the test.
     * It only attempts cleanup if a member was created (i.e., createdId is not null).
     *
     * @throws Exception if an error occurs during the HTTP request or response handling.
     */
    @AfterEach
    public void cleanUp() throws Exception {
        // Check if a member was created that needs to be cleaned up
        if (createdId != null) {
            log.info("Attempting cleanup of test member " + createdId + "...");
            
            // Create an HTTP DELETE request to remove the created member
            HttpRequest request = HttpRequest.newBuilder(getHTTPEndpoint().resolve("/api/members/" + createdId))
                    .header("Content-Type", "application/json") // Set the content type to JSON
                    .DELETE() // Specify that this is a DELETE request
                    .build(); // Build the request
            
            // Send the request and receive the response
            HttpResponse<String> response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
            
            // Log the response from the cleanup request
            log.info("Cleanup test member response: " + response);
        }
    }
}