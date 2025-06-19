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
package org.jboss.as.quickstarts.kitchensink.rest;

import jakarta.validation.ValidationException;
import org.jboss.as.quickstarts.kitchensink.data.MemberRepository;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.jboss.as.quickstarts.kitchensink.service.MemberRegistration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigInteger;
import java.util.List;
import java.util.logging.Logger;

/**
 * MemberResourceRESTService
 * <p/>
 * This class produces a RESTful service to read/write the contents of the members table.
 * It provides endpoints to list all members, lookup a member by ID, delete a member by ID,
 * and create a new member. The service utilizes the MemberRepository for data access and
 * MemberRegistration for member registration logic.
 * 
 * Design Patterns: This class follows the REST architectural pattern and uses the 
 * Dependency Injection pattern for managing dependencies.
 * 
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: 
 * - MemberRepository: Interface for member data access.
 * - Member: Model class representing a member.
 * - MemberRegistration: Service class for member registration logic.
 * 
 * Usage Example:
 * - To list all members: GET /api/members
 * - To create a new member: POST /api/members with Member JSON in the request body.
 * 
 * Thread Safety: This class is not thread-safe as it relies on the underlying 
 * repository and registration services to handle concurrency.
 */
@RestController
public class MemberResourceRESTService {
    
    // Logger instance for logging events and errors
    private final Logger log;
    
    // Repository for member data access
    private final MemberRepository repository;
    
    // Service for member registration logic
    private final MemberRegistration registration;

    /**
     * Constructor for MemberResourceRESTService.
     * 
     * @param log Logger instance for logging
     * @param repository MemberRepository instance for data access
     * @param registration MemberRegistration instance for registration logic
     */
    @Autowired
    public MemberResourceRESTService(Logger log, MemberRepository repository, MemberRegistration registration) {
        this.log = log; // Assigning the logger instance
        this.repository = repository; // Assigning the repository instance
        this.registration = registration; // Assigning the registration service instance
    }

    /**
     * Lists all members in the system.
     * 
     * @return List of all members
     */
    @GetMapping({"/api/members"})
    @ResponseBody
    public List<Member> listAllMembers() {
        // Fetching all members from the repository
        return repository.findAll(); // Returns the list of members
    }

    /**
     * Looks up a member by their ID.
     * 
     * @param id The ID of the member to look up
     * @return The member with the specified ID
     * @throws ResponseStatusException if the member is not found
     */
    @GetMapping("/api/members/{id:[0-9]+}")
    @ResponseBody
    public Member lookupMemberById(@PathVariable("id") long id) {
        // Fetching the member by ID from the repository
        Member member = repository.findById(BigInteger.valueOf(id));
        
        // Checking if the member was found
        if (member == null) {
            // Throwing an exception if the member is not found
            ResponseStatusException e = new ResponseStatusException(HttpStatus.NOT_FOUND, "Member not found");
            log.throwing(MemberResourceRESTService.class.getName(), "lookupMemberById", e); // Logging the exception
            throw e; // Propagating the exception
        }
        
        // Returning the found member
        return member; // Returns the member object
    }

    /**
     * Deletes a member by their ID.
     * 
     * @param id The ID of the member to delete
     * @throws ResponseStatusException if the member is not found
     */
    @DeleteMapping("/api/members/{id:[0-9]+}")
    public void deleteMemberById(@PathVariable("id") long id) {
        // Fetching the member by ID from the repository
        Member member = repository.findById(BigInteger.valueOf(id));
        
        // Checking if the member was found
        if (member == null) {
            // Throwing an exception if the member is not found
            ResponseStatusException e = new ResponseStatusException(HttpStatus.NOT_FOUND, "Member not found");
            log.throwing(MemberResourceRESTService.class.getName(), "deleteMemberById", e); // Logging the exception
            throw e; // Propagating the exception
        }
        
        // Deleting the member from the repository
        repository.deleteMemberById(BigInteger.valueOf(id)); // Deletes the member by ID
    }

    /**
     * Creates a new member from the provided values.
     * Performs validation and returns a response indicating success or failure.
     * 
     * @param member The member object to create
     * @return The created member object
     * @throws ResponseStatusException if validation fails or an internal error occurs
     */
    @PostMapping("/api/members")
    @ResponseStatus(HttpStatus.CREATED)
    @ResponseBody
    public Member createMember(@RequestBody Member member) {
        try {
            // Validating the member object
            validateMember(member); // Calls the validation method
            
            // Registering the member
            registration.register(member); // Registers the member
            
        } catch (ValidationException e) {
            // Handling validation exceptions
            ResponseStatusException error = new ResponseStatusException(HttpStatus.CONFLICT, "Email is already in use by another member");
            log.throwing(this.getClass().getName(), "createMember", error); // Logging the exception
            throw error; // Propagating the exception
        } catch (Exception e) {
            // Handling general exceptions
            ResponseStatusException error = new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
            log.throwing(this.getClass().getName(), "createMember", error); // Logging the exception
            throw error; // Propagating the exception
        }
        
        // Returning the created member
        return member; // Returns the created member object
    }

    /**
     * Validates the given Member object.
     * Throws a ValidationException if a member with the same email already exists.
     * 
     * @param member The member to validate
     * @throws ValidationException if a member with the same email already exists
     */
    private void validateMember(Member member) throws ValidationException {
        // Retrieving the email from the member object
        String email = member.getEmail();
        
        // Checking if the email already exists
        if (emailAlreadyExists(email)) {
            // Throwing a validation exception if the email is already in use
            ValidationException e = new ValidationException("Member already exists using email: " + email);
            log.throwing(this.getClass().getName(), "validateMember", e); // Logging the exception
            throw e; // Propagating the exception
        }
    }

    /**
     * Checks if a member with the same email address is already registered.
     * 
     * @param email The email to check
     * @return True if the email already exists, false otherwise
     */
    public boolean emailAlreadyExists(String email) {
        Member member = null; // Initializing member variable
        
        try {
            // Attempting to find a member by email
            member = repository.findByEmail(email); // Fetches the member by email
        } catch (Exception e) {
            // Ignoring exceptions during the lookup
        }
        
        // Returning true if a member was found, false otherwise
        return member != null; // Returns whether the member exists
    }
}