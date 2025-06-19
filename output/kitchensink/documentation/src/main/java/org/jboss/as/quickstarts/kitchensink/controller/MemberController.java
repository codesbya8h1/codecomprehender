/********************************************************************************
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
 ********************************************************************************/

package org.jboss.as.quickstarts.kitchensink.controller;

import jakarta.annotation.PostConstruct;
import jakarta.faces.application.FacesMessage;
import jakarta.faces.context.FacesContext;
import jakarta.faces.view.ViewScoped;
import org.jboss.as.quickstarts.kitchensink.data.MemberListProducer;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.jboss.as.quickstarts.kitchensink.service.MemberRegistration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;

import java.util.List;

/**
 * The MemberController class is responsible for managing member registration and
 * retrieval of member data in the application. It acts as a bridge between the
 * user interface and the underlying data model, facilitating the registration
 * process and maintaining the list of members.
 *
 * This class utilizes the Spring Framework's dependency injection to obtain
 * instances of MemberRegistration and MemberListProducer, which handle the
 * business logic and data access respectively.
 *
 * Design Patterns: This class follows the MVC (Model-View-Controller) pattern,
 * where it serves as the controller that processes user input and interacts
 * with the model.
 *
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 *
 * Related Classes:
 * - Member
 * - MemberRegistration
 * - MemberListProducer
 *
 * Usage Example:
 * To use this controller, it should be instantiated by the Spring framework,
 * and the methods can be called in response to user actions in the UI.
 *
 * Typical Workflow:
 * 1. A user fills out a registration form.
 * 2. The register() method is called to process the registration.
 * 3. The refresh() method is called to update the member list after registration.
 *
 * Thread Safety: This class is not thread-safe as it is designed to be used
 * within a single user session (ViewScoped).
 */
@Controller
@ViewScoped
public class MemberController {
    
    // MemberRegistration instance for handling member registration logic
    private final MemberRegistration memberRegistration;
    
    // MemberListProducer instance for retrieving and managing member data
    private final MemberListProducer memberListProducer;
    
    // New member instance to hold the data for the member being registered
    private Member newMember;
    
    // List of members retrieved from the data source
    private List<Member> members;

    /**
     * Constructor for MemberController that initializes the memberRegistration
     * and memberListProducer fields using dependency injection.
     *
     * @param memberRegistration An instance of MemberRegistration for handling
     *                          member registration logic.
     * @param memberListProducer An instance of MemberListProducer for managing
     *                          member data retrieval.
     */
    @Autowired
    public MemberController(MemberRegistration memberRegistration, MemberListProducer memberListProducer) {
        this.memberRegistration = memberRegistration; // Assigning the injected memberRegistration
        this.memberListProducer = memberListProducer; // Assigning the injected memberListProducer
    }

    /**
     * Initializes the controller after construction. This method is called
     * automatically after the constructor and is used to set up the initial
     * state of the controller.
     * 
     * It creates a new Member instance and retrieves the list of members
     * ordered by name from the memberListProducer.
     */
    @PostConstruct
    public void refresh() {
        newMember = new Member(); // Creating a new Member instance for registration
        memberListProducer.retrieveAllMembersOrderedByName(); // Retrieving all members ordered by name
        members = memberListProducer.getMembers(); // Storing the retrieved members in the members list
    }

    /**
     * Registers a new member using the memberRegistration service. This method
     * validates the member details and provides feedback to the user through
     * FacesMessages.
     *
     * @throws Exception if an error occurs during the registration process.
     */
    public void register() throws Exception {
        FacesContext facesContext = FacesContext.getCurrentInstance(); // Getting the current FacesContext
        
        // Checking if any of the member details are empty
        if (newMember.getName().isEmpty() || newMember.getEmail().isEmpty() || newMember.getPhoneNumber().isEmpty()) {
            // Adding an error message if validation fails
            facesContext.addMessage(null, new FacesMessage(FacesMessage.SEVERITY_ERROR, "Invalid member details", "One or more member details is blank"));
        }
        
        try {
            memberRegistration.register(newMember); // Attempting to register the new member
            
            // Creating a success message for successful registration
            FacesMessage msg = new FacesMessage(FacesMessage.SEVERITY_INFO, "Registered!", "Registration successful");
            facesContext.addMessage(null, msg); // Adding the success message to the context
            
            refresh(); // Refreshing the member list after successful registration
        } catch (Exception e) {
            // Handling any exceptions that occur during registration
            String errorMessage = getRootErrorMessage(e); // Getting the root error message from the exception
            FacesMessage msg = new FacesMessage(FacesMessage.SEVERITY_ERROR, errorMessage, "Registration unsuccessful");
            facesContext.addMessage(null, msg); // Adding the error message to the context
        }
    }

    /**
     * Retrieves the root cause error message from an exception. This method
     * traverses the exception chain to find the most relevant error message.
     *
     * @param e The exception from which to extract the root error message.
     * @return A string containing the root error message, or a default message
     *         if no message is found.
     */
    private String getRootErrorMessage(Exception e) {
        String errorMessage = "Registration failed"; // Default error message
        
        // Checking if the exception is null
        if (e == null) {
            return errorMessage; // Returning the default error message if no exception is provided
        }

        Throwable cause = e; // Starting with the provided exception
        // Looping through the cause chain to find the most specific error message
        while (cause != null) {
            errorMessage = cause.getLocalizedMessage(); // Updating the error message with the localized message
            cause = cause.getCause(); // Moving to the next cause in the chain
        }

        return errorMessage; // Returning the most relevant error message found
    }

    /**
     * Retrieves the list of members.
     *
     * @return A list of Member objects representing all registered members.
     */
    public List<Member> getMembers() {
        return members; // Returning the list of members
    }

    /**
     * Sets the list of members. This method is typically used for dependency
     * injection or when updating the member list.
     *
     * @param members A list of Member objects to set.
     */
    public void setMembers(List<Member> members) {
        this.members = members; // Assigning the provided list to the members field
    }

    /**
     * Retrieves the new member instance that is being registered.
     *
     * @return The Member object representing the new member.
     */
    public Member getNewMember() {
        return newMember; // Returning the new member instance
    }

    /**
     * Sets the new member instance. This method is typically used for
     * dependency injection or when updating the new member data.
     *
     * @param newMember The Member object to set as the new member.
     */
    public void setNewMember(Member newMember) {
        this.newMember = newMember; // Assigning the provided new member to the newMember field
    }
}