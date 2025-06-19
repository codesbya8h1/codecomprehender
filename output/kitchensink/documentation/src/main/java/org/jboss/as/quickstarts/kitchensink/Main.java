package org.jboss.as.quickstarts.kitchensink;

// Importing necessary classes for application configuration, data repository, logging, and Spring Boot functionalities
import org.jboss.as.quickstarts.kitchensink.config.ApplicationConfiguration;
import org.jboss.as.quickstarts.kitchensink.data.MemberRepository;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.mongo.MongoAutoConfiguration;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.context.annotation.Import;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;

/**
 * Main class for the Kitchensink application.
 * 
 * This class serves as the entry point for the Spring Boot application. It is responsible for 
 * initializing the application context and starting the application. The class extends 
 * SpringBootServletInitializer to support deployment in a servlet container.
 * 
 * Design Patterns: This class utilizes the Singleton pattern for the Spring application context.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023
 * 
 * Related Classes: 
 * - ApplicationConfiguration: Configuration class for application settings.
 * - MemberRepository: Data repository interface for member data access.
 * 
 * Usage Example:
 * To run the application, execute the main method. This will start the Spring Boot application 
 * and initialize the necessary components.
 * 
 * Thread Safety: The class is thread-safe as it relies on the Spring framework's 
 * thread-safe components.
 */
@SpringBootApplication // Annotation to mark this class as a Spring Boot application
@Import(value = MongoAutoConfiguration.class) // Importing MongoDB auto-configuration
@EnableMongoRepositories(basePackageClasses = MemberRepository.class) // Enabling MongoDB repositories
public class Main extends SpringBootServletInitializer {

    /**
     * Main method to launch the Spring Boot application.
     * 
     * This method initializes the Spring application context and starts the application.
     * It also includes error handling to log any exceptions that occur during startup.
     * 
     * @param args Command line arguments passed to the application. 
     *              Expected values are application-specific and can be used for configuration.
     * 
     * @throws Exception If an error occurs during application startup, it will be caught and logged.
     * 
     * Usage Example:
     * java -jar kitchensink.jar
     */
    public static void main(String[] args) {
        // Attempting to run the Spring application
        try {
            // Running the Spring application with the specified configuration class
            SpringApplication.run(ApplicationConfiguration.class, args);
        } catch (Exception e) {
            // Logging the error stack trace if an exception occurs during startup
            LoggerFactory.getLogger(Main.class).error(e.getStackTrace().toString(), e);
        }
    }
}