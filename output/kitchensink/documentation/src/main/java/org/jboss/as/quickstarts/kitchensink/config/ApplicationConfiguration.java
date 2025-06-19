package org.jboss.as.quickstarts.kitchensink.config;

// Import statements for required classes
import org.jboss.as.quickstarts.kitchensink.model.DatabaseSequence; // Model representing a database sequence
import org.jboss.as.quickstarts.kitchensink.model.Member; // Model representing a member
import org.springframework.beans.factory.annotation.Autowired; // Annotation for dependency injection
import org.springframework.boot.context.event.ApplicationReadyEvent; // Event triggered when the application is ready
import org.springframework.context.ApplicationListener; // Interface for listening to application events
import org.springframework.context.annotation.Bean; // Annotation for defining a bean
import org.springframework.context.annotation.Configuration; // Annotation for configuration classes
import org.springframework.data.mongodb.core.MongoOperations; // Interface for MongoDB operations
import org.springframework.data.mongodb.core.mapping.event.ValidatingMongoEventListener; // Listener for validating MongoDB events
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean; // Factory bean for local validation

/**
 * ApplicationConfiguration is a configuration class that sets up the necessary beans and initializes
 * the MongoDB collections for the application. It listens for the ApplicationReadyEvent to ensure
 * that the required collections are created in the database if they do not already exist.
 * 
 * This class uses the Spring Framework's dependency injection and event handling features.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023
 * 
 * Related Classes: DatabaseSequence, Member
 * 
 * Usage Example:
 * To use this configuration, simply include it in your Spring Boot application context. 
 * The MongoDB collections for DatabaseSequence and Member will be created automatically 
 * upon application startup if they do not exist.
 * 
 * Thread Safety: This class is not thread-safe as it is intended to be used during application startup.
 */
@Configuration
public class ApplicationConfiguration implements ApplicationListener<ApplicationReadyEvent> {

    // MongoOperations instance for performing operations on MongoDB
    private final MongoOperations mongoOperations;

    /**
     * Constructor for ApplicationConfiguration that initializes the MongoOperations instance.
     * 
     * @param mongoOperations An instance of MongoOperations used for database operations.
     *                        Must not be null.
     */
    @Autowired
    public ApplicationConfiguration(final MongoOperations mongoOperations) {
        // Assigning the provided MongoOperations instance to the class field
        this.mongoOperations = mongoOperations;
    }

    /**
     * This method is called when the ApplicationReadyEvent is published. It checks if the necessary
     * MongoDB collections exist and creates them if they do not.
     * 
     * @param event The ApplicationReadyEvent that indicates the application is ready.
     * 
     * @throws IllegalStateException if there is an issue with MongoDB operations.
     */
    @Override
    public void onApplicationEvent(final ApplicationReadyEvent event) {
        // Check if the collection for DatabaseSequence exists
        if (!mongoOperations.collectionExists(DatabaseSequence.class)) {
            // Create the collection for DatabaseSequence since it does not exist
            mongoOperations.createCollection(DatabaseSequence.class);
        }
        
        // Check if the collection for Member exists
        if (!mongoOperations.collectionExists(Member.class)) {
            // Create the collection for Member since it does not exist
            mongoOperations.createCollection(Member.class);
        }
    }

    /**
     * Defines a bean for ValidatingMongoEventListener which is used to validate MongoDB events.
     * 
     * @param factory The LocalValidatorFactoryBean used for validation.
     * 
     * @return A new instance of ValidatingMongoEventListener.
     */
    @Bean
    public ValidatingMongoEventListener validatingMongoEventListener(final LocalValidatorFactoryBean factory) {
        // Create and return a new ValidatingMongoEventListener with the provided factory
        return new ValidatingMongoEventListener(factory);
    }

    /**
     * Defines a bean for LocalValidatorFactoryBean which provides a local validation factory.
     * 
     * @return A new instance of LocalValidatorFactoryBean.
     */
    @Bean
    public LocalValidatorFactoryBean validator() {
        // Create and return a new LocalValidatorFactoryBean instance
        return new LocalValidatorFactoryBean();
    }
}