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
 * The MemberRepository interface provides methods for performing CRUD operations
 * on Member entities in a MongoDB database. It extends the MongoRepository interface
 * from Spring Data, which provides built-in methods for common database operations.
 * 
 * This repository follows the Repository design pattern, allowing for a clean separation
 * of the data access layer from the business logic layer.
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
 * Member member = memberRepository.findByEmail("example@example.com");
 * 
 * Thread Safety: 
 * This interface is not thread-safe. Implementations should handle concurrency as needed.
 */
package org.jboss.as.quickstarts.kitchensink.data;

import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.math.BigInteger;
import java.util.List;

/**
 * The MemberRepository interface extends MongoRepository to provide CRUD operations
 * for Member entities identified by a String ID. This interface defines custom query methods
 * to find members by their ID or email, retrieve all members ordered by name, and delete members
 * by their ID or email.
 */
@Repository
public interface MemberRepository extends MongoRepository<Member, String> {

    /**
     * Finds a Member by its unique identifier.
     *
     * @param id the unique identifier of the member as a BigInteger
     *           Must not be null.
     * @return the Member object if found, otherwise null.
     * @throws IllegalArgumentException if the id is null.
     */
    Member findById(BigInteger id);

    /**
     * Finds a Member by its email address.
     *
     * @param email the email address of the member as a String
     *              Must not be null or empty.
     * @return the Member object if found, otherwise null.
     * @throws IllegalArgumentException if the email is null or empty.
     */
    Member findByEmail(String email);

    /**
     * Retrieves all Members from the database, ordered by their name in ascending order.
     *
     * @return a List of Member objects, ordered by name.
     *         Returns an empty list if no members are found.
     */
    List<Member> findAllByOrderByNameAsc();

    /**
     * Deletes a Member by its unique identifier.
     *
     * @param id the unique identifier of the member as a BigInteger
     *           Must not be null.
     * @return the deleted Member object if found and deleted, otherwise null.
     * @throws IllegalArgumentException if the id is null.
     */
    Member deleteMemberById(BigInteger id);

    /**
     * Deletes a Member by its email address.
     *
     * @param email the email address of the member as a String
     *              Must not be null or empty.
     * @return the deleted Member object if found and deleted, otherwise null.
     * @throws IllegalArgumentException if the email is null or empty.
     */
    Member deleteMemberByEmail(String email);
}