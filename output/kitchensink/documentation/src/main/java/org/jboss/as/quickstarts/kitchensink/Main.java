package org.jboss.as.quickstarts.kitchensink;

// Import necessary classes for application configuration, logging, and MongoDB repository support
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
 * Design Patterns: This class follows the Singleton pattern for the Spring Boot application context.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023
 * 
 * Related Classes: 
 * - ApplicationConfiguration: Configuration class for application settings.
 * - MemberRepository: Repository interface for member data access.
 * 
 * Usage Example:
 * To run the application, execute the main method. This will start the Spring Boot application
 * and initialize the necessary components.
 * 
 * Thread Safety: The class is thread-safe as it is managed by the Spring framework.
 */
@SpringBootApplication
@Import(value = MongoAutoConfiguration.class) // Import MongoDB auto-configuration
@EnableMongoRepositories(basePackageClasses = MemberRepository.class) // Enable MongoDB repositories for MemberRepository
public class Main extends SpringBootServletInitializer {

    /**
     * Main method to run the Kitchensink application.
     * 
     * This method initializes the Spring application context and starts the application.
     * It handles any exceptions that may occur during the startup process and logs them.
     * 
     * @param args Command-line arguments passed to the application. Expected values can vary based on application needs.
     * 
     * @throws Exception If an error occurs during application startup, it will be caught and logged.
     * 
     * Usage Example:
     * java -jar kitchensink.jar
     */
    public static void main(String[] args) {
        // Try to run the Spring application with the specified configuration
        try {
            // Run the Spring application with the ApplicationConfiguration class and pass command-line arguments
            SpringApplication.run(ApplicationConfiguration.class, args);
        } catch (Exception e) {
            // Log the exception stack trace if an error occurs during startup
            LoggerFactory.getLogger(Main.class).error(e.getStackTrace().toString(), e);
        }
    }
}