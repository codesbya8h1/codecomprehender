package org.jboss.as.quickstarts.kitchensink.config;

// Import statements for required classes
import org.jboss.as.quickstarts.kitchensink.model.DatabaseSequence; // Model representing the database sequence
import org.jboss.as.quickstarts.kitchensink.model.Member; // Model representing a member in the application
import org.springframework.beans.factory.annotation.Autowired; // Annotation for dependency injection
import org.springframework.boot.context.event.ApplicationReadyEvent; // Event triggered when the application is ready
import org.springframework.context.ApplicationListener; // Interface for listening to application events
import org.springframework.context.annotation.Bean; // Annotation for defining a bean in the application context
import org.springframework.context.annotation.Configuration; // Annotation for marking a configuration class
import org.springframework.data.mongodb.core.MongoOperations; // Interface for MongoDB operations
import org.springframework.data.mongodb.core.mapping.event.ValidatingMongoEventListener; // Listener for validating MongoDB events
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean; // Factory bean for local validation

/**
 * ApplicationConfiguration is a configuration class that sets up the necessary beans and 
 * initializes the MongoDB collections required by the application. It listens for the 
 * ApplicationReadyEvent to ensure that the necessary collections are created in the 
 * MongoDB database when the application starts.
 * 
 * This class uses the Spring Framework's dependency injection and event handling 
 * capabilities to manage application startup behavior.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023-10-01
 * 
 * Related Classes: DatabaseSequence, Member
 * 
 * Usage Example:
 * The ApplicationConfiguration class is automatically picked up by Spring Boot during 
 * application startup, ensuring that the MongoDB collections are created as needed.
 * 
 * Thread Safety: This class is not thread-safe as it is intended to be used during 
 * application startup only.
 */
@Configuration
public class ApplicationConfiguration implements ApplicationListener<ApplicationReadyEvent> {

    // MongoOperations instance for performing operations on MongoDB
    private final MongoOperations mongoOperations;

    /**
     * Constructor for ApplicationConfiguration that initializes the MongoOperations instance.
     * 
     * @param mongoOperations An instance of MongoOperations used to interact with MongoDB.
     *                        This parameter must not be null.
     */
    @Autowired
    public ApplicationConfiguration(final MongoOperations mongoOperations) {
        // Assigning the provided MongoOperations instance to the class field
        this.mongoOperations = mongoOperations;
    }

    /**
     * This method is called when the ApplicationReadyEvent is published. It checks if the 
     * necessary collections for DatabaseSequence and Member exist in the MongoDB database, 
     * and creates them if they do not.
     * 
     * @param event The ApplicationReadyEvent that indicates the application is ready.
     *              This parameter must not be null.
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
     * Defines a bean for ValidatingMongoEventListener that uses the provided 
     * LocalValidatorFactoryBean for validation.
     * 
     * @param factory The LocalValidatorFactoryBean used for validation. This parameter must not be null.
     * @return A new instance of ValidatingMongoEventListener configured with the provided factory.
     */
    @Bean
    public ValidatingMongoEventListener validatingMongoEventListener(final LocalValidatorFactoryBean factory) {
        // Create and return a new ValidatingMongoEventListener with the provided factory
        return new ValidatingMongoEventListener(factory);
    }

    /**
     * Defines a bean for LocalValidatorFactoryBean which is used for validation purposes 
     * in the application.
     * 
     * @return A new instance of LocalValidatorFactoryBean for local validation.
     */
    @Bean
    public LocalValidatorFactoryBean validator() {
        // Create and return a new LocalValidatorFactoryBean instance
        return new LocalValidatorFactoryBean();
    }
}