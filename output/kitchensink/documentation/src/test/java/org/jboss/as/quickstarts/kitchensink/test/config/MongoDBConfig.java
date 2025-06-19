package org.jboss.as.quickstarts.kitchensink.test.config;

// Importing necessary Spring and Testcontainers classes
import org.springframework.context.annotation.Configuration;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;

/**
 * MongoDBConfig is a configuration class that sets up a MongoDB container 
 * for integration testing using Testcontainers. This class is responsible 
 * for initializing the MongoDB container and exposing the necessary ports 
 * for communication during tests.
 * 
 * <p>
 * The class utilizes the Singleton design pattern to ensure that only one 
 * instance of the MongoDB container is created and used throughout the 
 * application context. The container is configured to use the latest 
 * version of MongoDB and exposes the default MongoDB port (27017).
 * </p>
 * 
 * <p>
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023-10-01
 * </p>
 * 
 * <p>
 * Usage Example:
 * <pre>
 *     @SpringBootTest
 *     public class MyIntegrationTest {
 *         // Test methods that require MongoDB access can be defined here
 *     }
 * </pre>
 * </p>
 * 
 * <p>
 * Thread Safety: This class is not thread-safe as it initializes a static 
 * container that is shared across tests. Ensure that tests are run in a 
 * controlled environment to avoid conflicts.
 * </p>
 */
@Configuration
public class MongoDBConfig {

    // Declaring a static MongoDBContainer instance to manage the MongoDB lifecycle
    @Container
    public static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:latest")
            .withExposedPorts(27017); // Exposing the default MongoDB port

    // Static block to initialize the MongoDB container and set system properties
    static {
        // Starting the MongoDB container
        mongoDBContainer.start();

        // Retrieving the mapped port for the MongoDB container
        Integer port = mongoDBContainer.getMappedPort(27017);

        // Setting a system property to allow other components to access the MongoDB port
        System.setProperty("mongodb.container.port", String.valueOf(port));
    }
}