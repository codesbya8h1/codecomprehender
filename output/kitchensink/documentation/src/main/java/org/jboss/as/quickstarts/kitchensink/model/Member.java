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
 * This class encapsulates member details such as ID, email, name, and phone number.
 * 
 * Design Patterns: This class follows the Data Transfer Object (DTO) pattern,
 * allowing for easy transfer of member data between different layers of the application.
 * 
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: 
 * - MemberService: Service class for managing member operations.
 * - MemberRepository: Repository interface for database operations on Member entities.
 * 
 * Usage Example:
 * Member member = new Member();
 * member.setEmail("example@example.com");
 * member.setName("John Doe");
 * member.setPhoneNumber("1234567890");
 * 
 * Thread Safety: This class is not thread-safe. Instances of Member should be used
 * in a single-threaded context or synchronized externally when accessed by multiple threads.
 */
@Document(collection = "members")
public class Member implements Serializable {

    // Constant for the sequence name used for generating unique member IDs
    @Transient
    public static final String SEQUENCE_NAME = "members_sequence";

    // Unique identifier for the member, annotated with @Id for MongoDB
    @Id
    private BigInteger id;

    // Email of the member, must be non-empty, valid email format, and unique in the database
    @NotEmpty
    @Email
    @Indexed(unique = true)
    private String email;

    // Name of the member, must be non-empty, between 1 and 25 characters, and must not contain numbers
    @NotEmpty
    @Size(min = 1, max = 25)
    @Pattern(regexp = "[^0-9]*", message = "Must not contain numbers")
    private String name;

    // Phone number of the member, must be non-null, between 10 and 12 characters, and numeric
    @NotNull
    @Size(min = 10, max = 12)
    @Digits(fraction = 0, integer = 12)
    private String phoneNumber;

    /**
     * Gets the unique identifier of the member.
     * 
     * @return BigInteger representing the member's ID.
     */
    public BigInteger getId() {
        return id;
    }

    /**
     * Sets the unique identifier of the member.
     * 
     * @param id BigInteger representing the member's ID.
     *            Must be a valid non-null value.
     */
    public void setId(BigInteger id) {
        this.id = id; // Assign the provided ID to the member's ID field
    }

    /**
     * Gets the email of the member.
     * 
     * @return String representing the member's email.
     */
    public String getEmail() {
        return email;
    }

    /**
     * Sets the email of the member.
     * 
     * @param email String representing the member's email.
     *               Must be a valid non-empty email format.
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
        return name;
    }

    /**
     * Sets the name of the member.
     * 
     * @param name String representing the member's name.
     *             Must be non-empty and between 1 and 25 characters, without numbers.
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
        return phoneNumber;
    }

    /**
     * Sets the phone number of the member.
     * 
     * @param phoneNumber String representing the member's phone number.
     *                    Must be non-null and between 10 and 12 numeric characters.
     */
    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber; // Assign the provided phone number to the member's phone number field
    }
}