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
 * This class uses the Spring Framework's @Controller annotation to indicate that
 * it is a Spring-managed bean. It also uses the @ViewScoped annotation to ensure
 * that the state of the bean is maintained during the user's interaction with the
 * view.
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
 * To use this controller, it should be injected into a JSF view where member
 * registration is required. The methods provided can be called to register new
 * members and retrieve the list of existing members.
 *
 * Typical Workflow:
 * 1. A user fills out a registration form.
 * 2. The register() method is called to process the registration.
 * 3. If successful, the member list is refreshed.
 * 4. The user is notified of the registration status.
 *
 * Thread Safety:
 * This class is not thread-safe as it is designed to be used in a JSF context
 * where each user interaction is handled in a separate view scope.
 */
@Controller
@ViewScoped
public class MemberController {
    
    // MemberRegistration service for handling member registration logic
    private final MemberRegistration memberRegistration;
    
    // MemberListProducer for retrieving and managing the list of members
    private final MemberListProducer memberListProducer;
    
    // New member instance to hold data for registration
    private Member newMember;
    
    // List of existing members
    private List<Member> members;

    /**
     * Constructor for MemberController that initializes the member registration
     * and member list producer services.
     *
     * @param memberRegistration The service responsible for member registration.
     * @param memberListProducer The service responsible for producing the member list.
     */
    @Autowired
    public MemberController(MemberRegistration memberRegistration, MemberListProducer memberListProducer) {
        this.memberRegistration = memberRegistration; // Assigning the member registration service
        this.memberListProducer = memberListProducer; // Assigning the member list producer service
    }

    /**
     * Initializes the controller after construction. This method is called
     * automatically after the constructor and is used to set up the initial
     * state of the controller.
     *
     * It creates a new Member instance and retrieves the list of members
     * ordered by name.
     */
    @PostConstruct
    public void refresh() {
        newMember = new Member(); // Creating a new Member instance for registration
        memberListProducer.retrieveAllMembersOrderedByName(); // Retrieving all members ordered by name
        members = memberListProducer.getMembers(); // Storing the retrieved members in the list
    }

    /**
     * Registers a new member using the provided details. This method checks
     * for empty fields and attempts to register the member. It also handles
     * success and error messages.
     *
     * @throws Exception if an error occurs during registration.
     */
    public void register() throws Exception {
        FacesContext facesContext = FacesContext.getCurrentInstance(); // Getting the current FacesContext

        // Checking if any of the member details are empty
        if (newMember.getName().isEmpty() || newMember.getEmail().isEmpty() || newMember.getPhoneNumber().isEmpty()) {
            // Adding an error message to the FacesContext if details are invalid
            facesContext.addMessage(null, new FacesMessage(FacesMessage.SEVERITY_ERROR, "Invalid member details", "One or more member details is blank"));
        }

        try {
            memberRegistration.register(newMember); // Attempting to register the new member
            // Creating a success message for successful registration
            FacesMessage msg = new FacesMessage(FacesMessage.SEVERITY_INFO, "Registered!", "Registration successful");
            facesContext.addMessage(null, msg); // Adding the success message to the FacesContext
            refresh(); // Refreshing the member list after successful registration
        } catch (Exception e) {
            // Handling any exceptions that occur during registration
            String errorMessage = getRootErrorMessage(e); // Getting the root error message
            // Creating an error message for unsuccessful registration
            FacesMessage msg = new FacesMessage(FacesMessage.SEVERITY_ERROR, errorMessage, "Registration unsuccessful");
            facesContext.addMessage(null, msg); // Adding the error message to the FacesContext
        }
    }

    /**
     * Retrieves the root error message from an exception, traversing the cause
     * chain if necessary.
     *
     * @param e The exception from which to retrieve the error message.
     * @return A string containing the root error message.
     */
    private String getRootErrorMessage(Exception e) {
        String errorMessage = "Registration failed"; // Default error message
        if (e == null) {
            return errorMessage; // Returning default message if exception is null
        }

        Throwable cause = e; // Initializing cause with the provided exception
        // Looping through the cause chain to find the root cause message
        while (cause != null) {
            errorMessage = cause.getLocalizedMessage(); // Updating the error message with the localized message
            cause = cause.getCause(); // Moving to the next cause in the chain
        }

        return errorMessage; // Returning the final error message
    }

    /**
     * Gets the list of members.
     *
     * @return A list of Member objects representing the registered members.
     */
    public List<Member> getMembers() {
        return members; // Returning the list of members
    }

    /**
     * Sets the list of members.
     *
     * @param members A list of Member objects to set.
     */
    public void setMembers(List<Member> members) {
        this.members = members; // Assigning the provided list to the members field
    }

    /**
     * Gets the new member instance.
     *
     * @return The Member object representing the new member to be registered.
     */
    public Member getNewMember() {
        return newMember; // Returning the new member instance
    }

    /**
     * Sets the new member instance.
     *
     * @param newMember The Member object to set as the new member.
     */
    public void setNewMember(Member newMember) {
        this.newMember = newMember; // Assigning the provided new member to the field
    }
}