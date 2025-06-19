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
package org.jboss.as.quickstarts.kitchensink.data;

import jakarta.annotation.PostConstruct; // Importing PostConstruct for lifecycle management
import jakarta.enterprise.event.Observes; // Importing Observes for event handling
import jakarta.enterprise.event.Reception; // Importing Reception for event notification control
import org.jboss.as.quickstarts.kitchensink.model.Member; // Importing Member model class
import org.springframework.beans.factory.annotation.Autowired; // Importing Autowired for dependency injection
import org.springframework.stereotype.Component; // Importing Component for Spring component scanning

import java.util.List; // Importing List for member collection handling

/**
 * The MemberListProducer class is responsible for producing and managing a list of Member entities.
 * It interacts with the MemberRepository to retrieve members and observes events to update the member list.
 * 
 * Design Patterns: This class follows the Singleton pattern as it is managed by the Spring container.
 * 
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: Member, MemberRepository
 * 
 * Usage Example:
 * 
 * MemberListProducer memberListProducer = new MemberListProducer(memberRepository);
 * List<Member> members = memberListProducer.getMembers();
 * 
 * Typical Workflow:
 * 1. The application initializes the MemberListProducer.
 * 2. Upon initialization, it retrieves all members ordered by name.
 * 3. It listens for changes in the member list and updates accordingly.
 * 
 * Thread Safety: This class is not thread-safe as it relies on the Spring container for lifecycle management.
 */
@Component
public class MemberListProducer {
    
    // MemberRepository instance for accessing member data
    private final MemberRepository memberRepository;

    // List of members retrieved from the repository
    private List<Member> members;

    /**
     * Constructor for MemberListProducer.
     * 
     * @param memberRepository The repository used to access member data.
     *                         Must not be null.
     */
    @Autowired
    public MemberListProducer(MemberRepository memberRepository) {
        // Assigning the injected memberRepository to the class field
        this.memberRepository = memberRepository;
    }

    /**
     * Retrieves the list of members.
     * 
     * @return List<Member> A list of members. May return null if not initialized.
     */
    public List<Member> getMembers() {
        // Returning the current list of members
        return members;
    }

    /**
     * Observes changes to the member list and triggers a refresh of the member data.
     * 
     * @param member The member that has changed. This parameter is used to trigger the update.
     *               Can be null if no specific member is provided.
     */
    public void onMemberListChanged(@Observes(notifyObserver = Reception.IF_EXISTS) final Member member) {
        // Calling the method to retrieve all members ordered by name
        retrieveAllMembersOrderedByName();
    }

    /**
     * Initializes the member list by retrieving all members from the repository,
     * ordered by their names in ascending order.
     * This method is called after the constructor during the bean initialization phase.
     */
    @PostConstruct
    public void retrieveAllMembersOrderedByName() {
        // Fetching all members from the repository and ordering them by name in ascending order
        members = memberRepository.findAllByOrderByNameAsc();
    }
}