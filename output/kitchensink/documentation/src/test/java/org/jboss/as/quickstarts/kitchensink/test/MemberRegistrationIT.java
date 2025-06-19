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
 * MemberRegistrationIT is an integration test class that verifies the functionality of the MemberRegistration service.
 * This class uses Spring Boot's testing framework to load the application context and test the registration of a new member.
 * 
 * Design Patterns: This class follows the Dependency Injection pattern by using Spring's @Autowired annotation to inject dependencies.
 * 
 * Author: JBoss Community
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: 
 * - Member: Represents a member entity.
 * - MemberRegistration: Service responsible for member registration.
 * 
 * Usage Example:
 * To run this test, ensure that the application context is properly configured with MongoDB and the necessary beans are available.
 * 
 * Thread Safety: This class is not thread-safe as it is designed to run in a single-threaded test environment.
 */
@RunWith(SpringRunner.class)
@Testcontainers
@SpringBootTest(classes = {Main.class, MongoDBConfig.class})
public class MemberRegistrationIT {

    // MemberRegistration service used to register new members
    @Autowired
    MemberRegistration memberRegistration;

    // Logger instance for logging test information
    @Autowired
    Logger log;

    /**
     * Tests the registration of a new member.
     * This method creates a new Member object, sets its properties, and attempts to register it using the memberRegistration service.
     * 
     * Algorithm:
     * 1. Create a new Member instance and set its name, email, and phone number.
     * 2. Call the register method of memberRegistration to persist the new member.
     * 3. Assert that the member's ID is not null, indicating successful registration.
     * 4. Log the successful registration of the member.
     * 
     * @throws Exception if the registration process fails.
     * 
     * Performance Considerations: The performance of this test is dependent on the underlying database operations.
     * 
     * Usage Example:
     * This method can be executed as part of a test suite to validate member registration functionality.
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
            // If an exception occurs during registration, fail the test and log the error message
            fail(e.getMessage());
        }
    }
}