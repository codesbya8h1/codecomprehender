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

package org.jboss.as.quickstarts.kitchensink.data;

import jakarta.annotation.PostConstruct; // Importing PostConstruct for lifecycle management
import jakarta.enterprise.event.Observes; // Importing Observes for event handling
import jakarta.enterprise.event.Reception; // Importing Reception for observer notification control
import org.jboss.as.quickstarts.kitchensink.model.Member; // Importing Member model class
import org.springframework.beans.factory.annotation.Autowired; // Importing Autowired for dependency injection
import org.springframework.stereotype.Component; // Importing Component for Spring component scanning

import java.util.List; // Importing List for member collection handling

/**
 * The MemberListProducer class is responsible for producing a list of members
 * from the MemberRepository. It observes changes to the member list and updates
 * the internal list accordingly. This class is a Spring-managed component.
 * 
 * Design Patterns: This class follows the Singleton pattern as it is managed
 * by the Spring container, ensuring a single instance is used throughout the application.
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
 * 2. The producer retrieves all members ordered by name.
 * 3. Any changes to the member list trigger an update to the internal list.
 * 
 * Thread Safety: This class is not thread-safe. If accessed by multiple threads,
 * external synchronization is required.
 */
@Component
public class MemberListProducer {
    
    // MemberRepository instance for accessing member data
    private final MemberRepository memberRepository;

    // List to hold the members retrieved from the repository
    private List<Member> members;

    /**
     * Constructor for MemberListProducer.
     * 
     * @param memberRepository The MemberRepository instance used to fetch member data.
     *                        Must not be null.
     * 
     * This constructor is annotated with @Autowired, allowing Spring to inject
     * the MemberRepository dependency automatically.
     */
    @Autowired
    public MemberListProducer(MemberRepository memberRepository) {
        this.memberRepository = memberRepository; // Assigning the injected repository to the field
    }

    /**
     * Retrieves the list of members.
     * 
     * @return List<Member> A list of members. This may be empty if no members exist.
     */
    public List<Member> getMembers() {
        return members; // Returning the current list of members
    }

    /**
     * Observes changes to the member list and triggers a refresh of the member data.
     * 
     * @param member The member that has changed. This parameter is used to trigger
     *               the update but is not directly used in this method.
     * 
     * This method is called whenever a member is added, updated, or removed.
     * It invokes the retrieval of all members ordered by name.
     */
    public void onMemberListChanged(@Observes(notifyObserver = Reception.IF_EXISTS) final Member member) {
        // Calling the method to refresh the member list
        retrieveAllMembersOrderedByName();
    }

    /**
     * Initializes the member list by retrieving all members from the repository
     * and ordering them by name in ascending order.
     * 
     * This method is annotated with @PostConstruct, indicating that it should be
     * called after the constructor has completed and dependency injection is done.
     */
    @PostConstruct
    public void retrieveAllMembersOrderedByName() {
        // Fetching all members from the repository and ordering them by name
        members = memberRepository.findAllByOrderByNameAsc();
    }
}