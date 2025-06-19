package org.jboss.as.quickstarts.kitchensink.test.config;

// Importing necessary Spring and Testcontainers classes
import org.springframework.context.annotation.Configuration;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;

/**
 * MongoDBConfig is a configuration class that sets up a MongoDB container 
 * using Testcontainers for integration testing purposes. This class is 
 * annotated with @Configuration, indicating that it provides Spring 
 * configuration.
 * 
 * The MongoDB container is initialized with the latest MongoDB image 
 * and exposes the default MongoDB port (27017). The container is started 
 * statically, and the mapped port is set as a system property for 
 * accessibility in tests.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023-10-01
 * 
 * Related Classes: 
 * - MongoDBContainer (from Testcontainers)
 * 
 * Usage Example:
 * To use this configuration in your tests, simply include it in your 
 * Spring context. The MongoDB container will be automatically started 
 * before your tests run.
 * 
 * Thread Safety: 
 * This class is not thread-safe as it initializes a static container 
 * that is shared across tests. Ensure that tests are run in a controlled 
 * environment to avoid conflicts.
 */
@Configuration
public class MongoDBConfig {
    
    // Declaring a static MongoDBContainer instance to manage the MongoDB lifecycle
    @Container
    public static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:latest")
            .withExposedPorts(27017); // Exposing the default MongoDB port

    // Static block to start the MongoDB container and set system properties
    static {
        // Starting the MongoDB container
        mongoDBContainer.start();
        
        // Retrieving the mapped port for the MongoDB container
        Integer port = mongoDBContainer.getMappedPort(27017);
        
        // Setting the mapped port as a system property for use in tests
        System.setProperty("mongodb.container.port", String.valueOf(port));
    }
}