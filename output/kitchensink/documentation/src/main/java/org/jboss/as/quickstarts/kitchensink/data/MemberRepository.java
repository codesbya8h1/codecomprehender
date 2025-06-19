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

/**
 * The MemberRepository interface provides an abstraction for CRUD operations 
 * on Member entities stored in a MongoDB database. It extends the 
 * MongoRepository interface provided by Spring Data, which simplifies 
 * data access and manipulation.
 * 
 * This repository follows the Repository design pattern, allowing for 
 * separation of concerns between the data access layer and the business 
 * logic layer. It provides methods to find, delete, and retrieve 
 * Member entities based on various criteria.
 * 
 * Author: Red Hat, Inc.
 * Version: 1.0
 * Since: 2015
 * 
 * Related Classes: 
 * - Member: Represents a member entity in the application.
 * 
 * Usage Example:
 * 
 * MemberRepository memberRepository = ...; // Obtain an instance of MemberRepository
 * 
 * // Find a member by ID
 * Member member = memberRepository.findById(new BigInteger("1"));
 * 
 * // Find a member by email
 * Member memberByEmail = memberRepository.findByEmail("example@example.com");
 * 
 * // Retrieve all members ordered by name
 * List<Member> members = memberRepository.findAllByOrderByNameAsc();
 * 
 * // Delete a member by ID
 * memberRepository.deleteMemberById(new BigInteger("1"));
 * 
 * // Delete a member by email
 * memberRepository.deleteMemberByEmail("example@example.com");
 * 
 * Thread Safety: 
 * This interface is not thread-safe. Implementations should ensure 
 * thread safety if accessed by multiple threads concurrently.
 */
package org.jboss.as.quickstarts.kitchensink.data;

import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.math.BigInteger;
import java.util.List;

/**
 * MemberRepository interface that extends MongoRepository for 
 * performing CRUD operations on Member entities.
 */
@Repository
public interface MemberRepository extends MongoRepository<Member, String> {

    /**
     * Finds a Member entity by its unique identifier.
     *
     * @param id the unique identifier of the member as a BigInteger
     *           (must not be null)
     * @return the Member entity if found, or null if no member 
     *         with the given ID exists
     * @throws IllegalArgumentException if the id is null
     */
    Member findById(BigInteger id);

    /**
     * Finds a Member entity by its email address.
     *
     * @param email the email address of the member as a String
     *              (must not be null or empty)
     * @return the Member entity if found, or null if no member 
     *         with the given email exists
     * @throws IllegalArgumentException if the email is null or empty
     */
    Member findByEmail(String email);

    /**
     * Retrieves all Member entities ordered by their name in ascending order.
     *
     * @return a List of Member entities sorted by name
     *         (may be empty if no members exist)
     */
    List<Member> findAllByOrderByNameAsc();

    /**
     * Deletes a Member entity by its unique identifier.
     *
     * @param id the unique identifier of the member as a BigInteger
     *           (must not be null)
     * @return the deleted Member entity, or null if no member 
     *         with the given ID exists
     * @throws IllegalArgumentException if the id is null
     */
    Member deleteMemberById(BigInteger id);

    /**
     * Deletes a Member entity by its email address.
     *
     * @param email the email address of the member as a String
     *              (must not be null or empty)
     * @return the deleted Member entity, or null if no member 
     *         with the given email exists
     * @throws IllegalArgumentException if the email is null or empty
     */
    Member deleteMemberByEmail(String email);
}