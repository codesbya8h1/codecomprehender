/*
 * JBoss, Home of Professional Open Source
 * Copyright 2015, Red Hat, Inc. and/or its affiliates, and individual
 * contributors by the @authors tag. See the copyright.txt in the
 * distribution for a full listing of individual contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * you may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.jboss.as.quickstarts.kitchensink.model;

import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Transient;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.io.Serializable;
import java.math.BigInteger;

/**
 * The Member class represents a member entity in the application.
 * It is mapped to a MongoDB document in the "members" collection.
 * This class implements Serializable to allow for object serialization.
 * 
 * Design Patterns: This class follows the Data Transfer Object (DTO) pattern,
 * encapsulating member data and providing getter and setter methods for access.
 * 
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: 
 * - This class is related to the database operations that manage member entities.
 * 
 * Usage Example:
 * Member member = new Member();
 * member.setEmail("example@example.com");
 * member.setName("John Doe");
 * member.setPhoneNumber("1234567890");
 * 
 * Thread Safety: This class is not thread-safe as it does not implement any 
 * synchronization mechanisms. It is intended for use in a single-threaded context 
 * or where external synchronization is provided.
 */
@Document(collection = "members") // Indicates that this class is a MongoDB document
public class Member implements Serializable {

    @Transient // Indicates that this field should not be persisted in the database
    public static final String SEQUENCE_NAME = "members_sequence"; // Constant for the sequence name

    @Id // Marks this field as the primary key for the MongoDB document
    private BigInteger id; // Unique identifier for the member

    @NotEmpty // Validation constraint ensuring the email is not empty
    @Email // Validation constraint ensuring the email is a valid email format
    @Indexed(unique = true) // Ensures that the email field is unique in the database
    private String email; // Email address of the member

    @NotEmpty // Validation constraint ensuring the name is not empty
    @Size(min = 1, max = 25) // Validation constraint ensuring the name length is between 1 and 25 characters
    @Pattern(regexp = "[^0-9]*", message = "Must not contain numbers") // Validation constraint ensuring the name does not contain numbers
    private String name; // Name of the member

    @NotNull // Validation constraint ensuring the phone number is not null
    @Size(min = 10, max = 12) // Validation constraint ensuring the phone number length is between 10 and 12 characters
    @Digits(fraction = 0, integer = 12) // Validation constraint ensuring the phone number is a valid integer
    private String phoneNumber; // Phone number of the member

    /**
     * Gets the unique identifier of the member.
     * 
     * @return BigInteger representing the member's ID.
     */
    public BigInteger getId() {
        return id; // Return the member's ID
    }

    /**
     * Sets the unique identifier of the member.
     * 
     * @param id BigInteger representing the member's ID.
     */
    public void setId(BigInteger id) {
        this.id = id; // Assign the provided ID to the member's ID field
    }

    /**
     * Gets the email address of the member.
     * 
     * @return String representing the member's email address.
     */
    public String getEmail() {
        return email; // Return the member's email address
    }

    /**
     * Sets the email address of the member.
     * 
     * @param email String representing the member's email address.
     */
    public void setEmail(String email) {
        this.email = email; // Assign the provided email to the member's email field
    }

    /**
     * Gets the name of the member.
     * 
     * @return String representing the member's name.
     */
    public String getName() {
        return name; // Return the member's name
    }

    /**
     * Sets the name of the member.
     * 
     * @param name String representing the member's name.
     */
    public void setName(String name) {
        this.name = name; // Assign the provided name to the member's name field
    }

    /**
     * Gets the phone number of the member.
     * 
     * @return String representing the member's phone number.
     */
    public String getPhoneNumber() {
        return phoneNumber; // Return the member's phone number
    }

    /**
     * Sets the phone number of the member.
     * 
     * @param phoneNumber String representing the member's phone number.
     */
    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber; // Assign the provided phone number to the member's phone number field
    }
}