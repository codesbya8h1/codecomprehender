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
 * correctly via the HTTP API.
 *
 * This class uses the JUnit 5 testing framework and follows the Arrange-Act-Assert pattern for structuring tests.
 * It also utilizes the HttpClient for making HTTP requests to the server.
 *
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 *
 * Related Classes:
 * - Member: Represents a member in the application.
 *
 * Usage Example:
 * To run the tests, use a JUnit-compatible test runner. Ensure that the server is running and accessible.
 *
 * Thread Safety:
 * This class is not thread-safe as it maintains state in the form of the createdId field.
 */
public class RemoteMemberRegistrationIT {

    // Logger instance for logging test activities
    private static final Logger log = Logger.getLogger(RemoteMemberRegistrationIT.class.getName());

    // Holds the ID of the created member for cleanup purposes
    private BigInteger createdId;

    /**
     * Retrieves the HTTP endpoint for member registration.
     *
     * This method constructs the URI for the member registration API endpoint.
     * It first attempts to get the server host from the environment variable
     * or system property. If neither is set, it defaults to "http://localhost:8080".
     *
     * @return URI of the member registration endpoint
     * @throws RuntimeException if the URI syntax is incorrect
     */
    protected URI getHTTPEndpoint() {
        // Retrieve the server host
        String host = getServerHost();
        
        // If the host is not set, default to localhost
        if (host == null) {
            host = "http://localhost:8080";
        }
        
        // Attempt to create a URI from the host and endpoint path
        try {
            return new URI(host + "/api/members");
        } catch (URISyntaxException ex) {
            // Throw a runtime exception if URI syntax is invalid
            throw new RuntimeException(ex);
        }
    }

    /**
     * Retrieves the server host from environment variables or system properties.
     *
     * This method checks for the "SERVER_HOST" environment variable first,
     * and if not found, it checks the "server.host" system property.
     *
     * @return String representing the server host, or null if not set
     */
    private String getServerHost() {
        // Check for the SERVER_HOST environment variable
        String host = System.getenv("SERVER_HOST");
        
        // If not found, check for the server.host system property
        if (host == null) {
            host = System.getProperty("server.host");
        }
        
        // Return the host value
        return host;
    }

    /**
     * Tests the registration of a new member.
     *
     * This test creates a new member with predefined attributes, sends a POST
     * request to the member registration endpoint, and asserts that the response
     * status code is 201 (Created). It also logs the created member's details.
     *
     * @throws Exception if an error occurs during the HTTP request
     */
    @Test
    public void testRegister() throws Exception {
        // Create a new Member object
        Member newMember = new Member();
        
        // Set the member's name
        newMember.setName("Jane Doe");
        
        // Set the member's email
        newMember.setEmail("jane@mailinator.com");
        
        // Set the member's phone number
        newMember.setPhoneNumber("2125551234");
        
        // Build a JSON object representing the new member
        JsonObject json = Json.createObjectBuilder()
                .add("name", "Jane Doe") // Add name to JSON
                .add("email", "jane@mailinator.com") // Add email to JSON
                .add("phoneNumber", "2125551234") // Add phone number to JSON
                .build(); // Build the JSON object
        
        // Create an HTTP POST request to the member registration endpoint
        HttpRequest request = HttpRequest.newBuilder(getHTTPEndpoint())
                .header("Content-Type", "application/json") // Set content type to JSON
                .POST(HttpRequest.BodyPublishers.ofString(json.toString())) // Set the request body
                .build(); // Build the request
        
        // Send the request and receive the response
        HttpResponse<String> response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
        
        // Assert that the response status code is 201 (Created)
        Assert.assertEquals(201, response.statusCode());
        
        // Parse the response body as a JSON object
        JSONObject jsonObject = new JSONObject(response.body().toString());
        
        // Log the details of the created member
        log.info("Member was created: " + jsonObject);
        
        // Store the created member's ID for cleanup
        createdId = new BigInteger(jsonObject.getString("id"));
    }

    /**
     * Cleans up the created member after each test.
     *
     * This method sends a DELETE request to remove the member created during
     * the test if it exists. It logs the cleanup attempt and the response.
     *
     * @throws Exception if an error occurs during the HTTP request
     */
    @AfterEach
    public void cleanUp() throws Exception {
        // Check if a member was created
        if (createdId != null) {
            // Log the cleanup attempt for the created member
            log.info("Attempting cleanup of test member " + createdId + "...");
            
            // Create an HTTP DELETE request to remove the member
            HttpRequest request = HttpRequest.newBuilder(getHTTPEndpoint().resolve("/api/members/" + createdId))
                    .header("Content-Type", "application/json") // Set content type to JSON
                    .DELETE() // Specify the DELETE method
                    .build(); // Build the request
            
            // Send the request and receive the response
            HttpResponse<String> response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
            
            // Log the response from the cleanup request
            log.info("Cleanup test member response: " + response);
        }
    }
}