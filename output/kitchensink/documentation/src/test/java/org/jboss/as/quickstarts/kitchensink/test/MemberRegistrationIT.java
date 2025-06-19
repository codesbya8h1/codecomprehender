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

import org.jboss.as.quickstarts.kitchensink.Main;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.jboss.as.quickstarts.kitchensink.service.MemberRegistration;
import org.jboss.as.quickstarts.kitchensink.test.config.MongoDBConfig;
import org.junit.jupiter.api.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.logging.Logger;

/**
 * MemberRegistrationIT is an integration test class for testing the MemberRegistration service.
 * This class uses Spring Boot's testing framework to load the application context and 
 * perform tests on the member registration functionality.
 * 
 * The class is annotated with @RunWith(SpringRunner.class) to enable Spring's testing support,
 * and @Testcontainers to indicate that it uses Testcontainers for integration testing.
 * 
 * The tests are executed in a Spring Boot context that includes the Main application class 
 * and MongoDB configuration.
 * 
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: 
 * - Main: The main application class for the kitchensink application.
 * - Member: The model class representing a member.
 * - MemberRegistration: The service class responsible for member registration.
 * 
 * Usage Example:
 * To run this test, execute the test suite using a compatible test runner that supports JUnit.
 * Typical workflow involves running this test to ensure that member registration works as expected.
 * 
 * Thread Safety: 
 * This class is not thread-safe as it is designed for single-threaded test execution.
 */
@RunWith(SpringRunner.class)
@Testcontainers
@SpringBootTest(classes = {Main.class, MongoDBConfig.class})
public class MemberRegistrationIT {

    // Autowired MemberRegistration service for registering members
    @Autowired
    MemberRegistration memberRegistration;

    // Autowired Logger for logging test information
    @Autowired
    Logger log;

    /**
     * Tests the member registration functionality.
     * 
     * This method creates a new Member instance, sets its properties, and attempts to register it
     * using the memberRegistration service. It verifies that the member is successfully registered 
     * by checking that the ID is not null after registration.
     * 
     * @throws Exception if the registration process fails
     * 
     * Expected Behavior:
     * - A new member is created and registered.
     * - The member's ID should be generated and not null after registration.
     * 
     * Exception Handling:
     * If any exception occurs during the registration process, the test will fail with the exception message.
     */
    @Test
    public void testRegister() {
        // Create a new Member instance to be registered
        Member newMember = new Member();
        
        // Set the name of the new member
        newMember.setName("Jane Doe");
        
        // Set the email of the new member
        newMember.setEmail("jane@mailinator.com");
        
        // Set the phone number of the new member
        newMember.setPhoneNumber("2125551234");
        
        // Attempt to register the new member
        try {
            // Call the register method of memberRegistration to persist the new member
            memberRegistration.register(newMember);
            
            // Assert that the new member's ID is not null, indicating successful registration
            assertNotNull(newMember.getId());
            
            // Log the successful registration of the new member with their ID
            log.info(newMember.getName() + " was persisted with id " + newMember.getId());
        } catch (Exception e) {
            // If an exception occurs, fail the test and log the exception message
            fail(e.getMessage());
        }
    }
}