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
 * manage unique sequence generation for member IDs.
 * 
 * This class uses the Singleton design pattern to ensure that only one instance of 
 * MemberRegistration exists within the application context.
 * 
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: 
 * - MemberRepository: Interface for member data access.
 * - DatabaseSequence: Model representing the sequence for generating unique IDs.
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
 * environment to avoid race conditions during member registration.
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
     * @param mongoOperations The MongoOperations instance used for MongoDB interactions.
     * @param memberRepository The MemberRepository instance for member data access.
     * @param mongo The MongoClient instance for MongoDB connection (not used directly).
     */
    @Autowired
    public MemberRegistration(final MongoOperations mongoOperations, final MemberRepository memberRepository, MongoClient mongo) {
        // Initialize the logger for this class
        log = Logger.getLogger(getClass().getName());
        
        // Assign the provided MongoOperations instance to the class field
        this.mongoOperations = mongoOperations;
        
        // Assign the provided MemberRepository instance to the class field
        this.memberRepository = memberRepository;
    }

    /**
     * Registers a new member in the system.
     * 
     * @param member The Member object containing the details of the member to be registered.
     * @throws Exception if there is an error during registration, such as a MongoDB write error.
     * 
     * This method generates a unique ID for the member using the generateSequence method,
     * then attempts to insert the member into the database. If a MongoWriteException occurs,
     * it wraps the exception and throws a generic Exception with the error message.
     */
    public void register(Member member) throws Exception {
        // Generate a unique ID for the member using the sequence generator
        member.setId(generateSequence(Member.SEQUENCE_NAME));
        
        try {
            // Attempt to insert the new member into the repository
            memberRepository.insert(member);
        } catch (MongoWriteException e) {
            // If a MongoWriteException occurs, throw a new Exception with the error message
            throw new Exception(e.getLocalizedMessage());
        }
    }

    /**
     * Generates a unique sequence number for a given sequence name.
     * 
     * @param sequenceName The name of the sequence to be generated.
     * @return A BigInteger representing the next sequence number.
     * 
     * This method uses MongoDB's findAndModify operation to atomically increment the sequence
     * number in the database. If the sequence does not exist, it initializes it to 1.
     */
    private BigInteger generateSequence(String sequenceName) {
        // Create a query to find the sequence document by its ID
        DatabaseSequence counter = mongoOperations.findAndModify(
                Query.query(Criteria.where("_id").is(sequenceName)), // Query to find the sequence by ID
                new Update().inc("sequence", 1), // Increment the sequence field by 1
                FindAndModifyOptions.options().returnNew(true).upsert(true), // Options to return the new value and upsert if not found
                DatabaseSequence.class // The class type of the document to return
        );
        
        // Return the new sequence value if found, otherwise return BigInteger.ONE
        return !Objects.isNull(counter) ? counter.getSequence() : BigInteger.ONE;
    }
}