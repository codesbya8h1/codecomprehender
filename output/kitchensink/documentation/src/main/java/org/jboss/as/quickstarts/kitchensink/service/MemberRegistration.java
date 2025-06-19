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
package org.jboss.as.quickstarts.kitchensink.service;

import com.mongodb.MongoWriteException;
import com.mongodb.client.MongoClient;
import org.jboss.as.quickstarts.kitchensink.data.MemberRepository;
import org.jboss.as.quickstarts.kitchensink.model.DatabaseSequence;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.mongodb.core.FindAndModifyOptions;
import org.springframework.data.mongodb.core.MongoOperations;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Service;

import java.math.BigInteger;
import java.util.Objects;
import java.util.logging.Logger;

/**
 * The MemberRegistration class is responsible for handling the registration of new members
 * in the system. It interacts with the MongoDB database to store member information and
 * manage unique member identifiers through a sequence generator.
 *
 * This class follows the Service design pattern, encapsulating the business logic related
 * to member registration. It utilizes Spring's dependency injection to manage its dependencies.
 *
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 *
 * Related Classes:
 * - MemberRepository: Interface for member data access.
 * - DatabaseSequence: Model representing the sequence generator for unique IDs.
 * - Member: Model representing a member entity.
 *
 * Usage Example:
 * MemberRegistration memberRegistration = new MemberRegistration(mongoOperations, memberRepository, mongoClient);
 * Member newMember = new Member();
 * newMember.setName("John Doe");
 * memberRegistration.register(newMember);
 *
 * Thread Safety: This class is not thread-safe as it relies on MongoDB operations that are
 * inherently thread-safe. However, care should be taken when using this class in a multi-threaded
 * environment to ensure that member registration is handled correctly.
 */
@Service
public class MemberRegistration {
    
    // Logger instance for logging events and errors
    private final Logger log;

    // MongoOperations instance for performing MongoDB operations
    private final MongoOperations mongoOperations;

    // MemberRepository instance for accessing member data
    private final MemberRepository memberRepository;

    /**
     * Constructor for MemberRegistration.
     *
     * @param mongoOperations the MongoOperations instance used for MongoDB interactions
     * @param memberRepository the MemberRepository instance for member data access
     * @param mongo the MongoClient instance for MongoDB connection (not used directly)
     */
    @Autowired
    public MemberRegistration(final MongoOperations mongoOperations, final MemberRepository memberRepository, MongoClient mongo) {
        // Initialize the logger for this class
        log = Logger.getLogger(getClass().getName());
        
        // Assign the MongoOperations instance to the class field
        this.mongoOperations = mongoOperations;
        
        // Assign the MemberRepository instance to the class field
        this.memberRepository = memberRepository;
    }

    /**
     * Registers a new member in the system.
     *
     * This method generates a unique ID for the member using a sequence generator,
     * then attempts to insert the member into the database. If the insertion fails,
     * an exception is thrown.
     *
     * @param member the Member object to be registered
     * @throws Exception if there is an error during member registration, such as a write error
     */
    public void register(Member member) throws Exception {
        // Generate a unique ID for the member using the sequence generator
        member.setId(generateSequence(Member.SEQUENCE_NAME));
        
        // Attempt to insert the member into the repository
        try {
            memberRepository.insert(member);
        } catch (MongoWriteException e) {
            // If a MongoWriteException occurs, throw a new Exception with the error message
            throw new Exception(e.getLocalizedMessage());
        }
    }

    /**
     * Generates a unique sequence number for a given sequence name.
     *
     * This method retrieves and increments the sequence number from the database.
     * If the sequence does not exist, it initializes it to 1.
     *
     * @param sequenceName the name of the sequence to generate
     * @return a BigInteger representing the next sequence number
     */
    private BigInteger generateSequence(String sequenceName) {
        // Create a query to find the sequence document by its ID
        Query query = Query.query(Criteria.where("_id").is(sequenceName));
        
        // Create an update operation to increment the sequence by 1
        Update update = new Update().inc("sequence", 1);
        
        // Define options for the find and modify operation
        FindAndModifyOptions options = FindAndModifyOptions.options().returnNew(true).upsert(true);
        
        // Execute the find and modify operation to get the updated sequence
        DatabaseSequence counter = mongoOperations.findAndModify(
                query,
                update,
                options,
                DatabaseSequence.class
        );
        
        // Return the new sequence number or 1 if the counter is null
        return !Objects.isNull(counter) ? counter.getSequence() : BigInteger.ONE;
    }
}