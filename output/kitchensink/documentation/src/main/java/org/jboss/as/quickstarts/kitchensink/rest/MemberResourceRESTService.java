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
 * MemberResourceRESTService is a RESTful service that provides endpoints to manage members in the system.
 * <p>
 * This class allows clients to perform CRUD operations on members, including creating new members,
 * retrieving member details, and deleting members. It uses Spring's REST capabilities and is designed
 * to interact with a member repository for data persistence.
 * </p>
 * 
 * <p>
 * The service is thread-safe as it does not maintain any mutable state and relies on stateless
 * components for its operations.
 * </p>
 * 
 * <p>
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * </p>
 * 
 * <p>
 * Related Classes: Member, MemberRepository, MemberRegistration
 * </p>
 * 
 * <p>
 * Usage Example:
 * <pre>
 *     MemberResourceRESTService service = new MemberResourceRESTService(logger, memberRepository, memberRegistration);
 *     List<Member> members = service.listAllMembers();
 * </pre>
 * </p>
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
     * @param registration MemberRegistration instance for handling member registration
     */
    @Autowired
    public MemberResourceRESTService(Logger log, MemberRepository repository, MemberRegistration registration) {
        this.log = log; // Assign the logger instance
        this.repository = repository; // Assign the member repository
        this.registration = registration; // Assign the member registration service
    }

    /**
     * Retrieves a list of all members.
     * 
     * @return List of Member objects representing all members in the repository
     */
    @GetMapping({"/api/members"})
    @ResponseBody
    public List<Member> listAllMembers() {
        // Fetch all members from the repository
        return repository.findAll(); // Return the list of members
    }

    /**
     * Looks up a member by their unique identifier.
     * 
     * @param id The unique identifier of the member to look up
     * @return Member object representing the found member
     * @throws ResponseStatusException if the member is not found
     */
    @GetMapping("/api/members/{id:[0-9]+}")
    @ResponseBody
    public Member lookupMemberById(@PathVariable("id") long id) {
        // Attempt to find the member by ID
        Member member = repository.findById(BigInteger.valueOf(id));
        
        // Check if the member was found
        if (member == null) {
            // Create a new exception indicating the member was not found
            ResponseStatusException e = new ResponseStatusException(HttpStatus.NOT_FOUND, "Member not found");
            // Log the exception for debugging purposes
            log.throwing(MemberResourceRESTService.class.getName(), "deleteMemberById", e);
            // Throw the exception to indicate the error
            throw e;
        }
        
        // Return the found member
        return member;
    }

    /**
     * Deletes a member by their unique identifier.
     * 
     * @param id The unique identifier of the member to delete
     * @throws ResponseStatusException if the member is not found
     */
    @DeleteMapping("/api/members/{id:[0-9]+}")
    public void deleteMemberById(@PathVariable("id") long id) {
        // Attempt to find the member by ID
        Member member = repository.findById(BigInteger.valueOf(id));
        
        // Check if the member was found
        if (member == null) {
            // Create a new exception indicating the member was not found
            ResponseStatusException e = new ResponseStatusException(HttpStatus.NOT_FOUND, "Member not found");
            // Log the exception for debugging purposes
            log.throwing(MemberResourceRESTService.class.getName(), "deleteMemberById", e);
            // Throw the exception to indicate the error
            throw e;
        }
        
        // Delete the member from the repository
        repository.deleteMemberById(BigInteger.valueOf(id)); // Perform the deletion
    }

    /**
     * Creates a new member from the provided values.
     * <p>
     * Performs validation and returns a response indicating the result of the operation.
     * </p>
     * 
     * @param member The Member object containing the details of the new member
     * @return The created Member object
     * @throws ResponseStatusException if validation fails or an internal error occurs
     */
    @PostMapping("/api/members")
    @ResponseStatus(HttpStatus.CREATED)
    @ResponseBody
    public Member createMember(@RequestBody Member member) {
        try {
            // Validate the member details
            validateMember(member);
            // Register the new member
            registration.register(member);
        } catch (ValidationException e) {
            // Handle validation exceptions specifically
            ResponseStatusException error = new ResponseStatusException(HttpStatus.CONFLICT, "Email is already in use by another member");
            // Log the exception for debugging purposes
            log.throwing(this.getClass().getName(), "createMember", error);
            // Throw the exception to indicate the error
            throw error;
        } catch (Exception e) {
            // Handle any other exceptions that may occur
            ResponseStatusException error = new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
            // Log the exception for debugging purposes
            log.throwing(this.getClass().getName(), "createMember", error);
            // Throw the exception to indicate the error
            throw error;
        }
        // Return the created member
        return member;
    }

    /**
     * Validates the given Member object to ensure it meets the required criteria.
     * 
     * @param member The Member object to be validated
     * @throws ValidationException If a member with the same email already exists
     */
    private void validateMember(Member member) throws ValidationException {
        // Retrieve the email from the member object
        String email = member.getEmail();
        
        // Check if the email already exists in the repository
        if (emailAlreadyExists(email)) {
            // Create a new validation exception indicating the email is already in use
            ValidationException e = new ValidationException("Member already exists using email: " + email);
            // Log the exception for debugging purposes
            log.throwing(this.getClass().getName(), "validateMember", e);
            // Throw the exception to indicate the validation error
            throw e;
        }
    }

    /**
     * Checks if a member with the same email address is already registered.
     * 
     * @param email The email address to check for existence
     * @return True if the email already exists, false otherwise
     */
    public boolean emailAlreadyExists(String email) {
        Member member = null; // Initialize member variable to hold the found member
        try {
            // Attempt to find a member by email
            member = repository.findByEmail(email);
        } catch (Exception e) {
            // Ignore any exceptions that occur during the lookup
        }
        // Return true if a member was found, false otherwise
        return member != null; // Check if the member is not null
    }
}