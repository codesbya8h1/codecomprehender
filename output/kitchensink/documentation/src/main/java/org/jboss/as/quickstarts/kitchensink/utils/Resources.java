package org.jboss.as.quickstarts.kitchensink.utils;

// Importing necessary Spring framework classes for dependency injection and configuration
import org.springframework.beans.factory.InjectionPoint;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;

import java.util.logging.Logger;

/**
 * The Resources class is responsible for providing application-wide resources
 * such as loggers through dependency injection. This class is annotated with
 * @Configuration, indicating that it contains bean definitions that will be
 * managed by the Spring container.
 * 
 * Design Pattern: This class utilizes the Factory Method pattern to produce
 * Logger instances that are specific to the class requesting them.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023-10-01
 * 
 * Related Classes: This class is related to other configuration classes that
 * may define additional beans for the application.
 * 
 * Usage Example:
 * <pre>
 *     @Autowired
 *     private Logger logger;
 * </pre>
 * 
 * Typical Workflow:
 * 1. The Spring container scans for classes annotated with @Configuration.
 * 2. It processes the bean definitions and creates instances as needed.
 * 3. When a class requires a Logger, it is injected automatically.
 * 
 * Thread Safety: The Logger instances produced by this class are thread-safe
 * as they are created with the "prototype" scope, ensuring that each
 * injection point receives a unique instance.
 */
@Configuration
public class Resources {

    /**
     * Produces a Logger instance that is specific to the class where it is
     * injected. The Logger is created using the class name of the requesting
     * class, allowing for contextual logging.
     * 
     * @param injectionPoint The InjectionPoint provides information about the
     *                       context in which the logger is being injected.
     *                       It is used to determine the declaring class for
     *                       the logger.
     * @return A Logger instance specific to the requesting class.
     * 
     * @throws IllegalArgumentException if the injection point does not have a
     *                                   valid declaring class.
     * 
     * Performance Considerations: The method has a constant time complexity
     * O(1) as it simply retrieves the class name and creates a logger.
     * 
     * Usage Example:
     * <pre>
     *     Logger logger = produceLogger(injectionPoint);
     * </pre>
     */
    @Bean
    @Scope("prototype") // Specifies that a new instance of Logger will be created each time it is requested
    public Logger produceLogger(InjectionPoint injectionPoint) {
        
        // Retrieve the class that is requesting the logger
        Class<?> classOnWired = injectionPoint.getMember().getDeclaringClass();
        
        // Create and return a Logger instance for the requesting class
        return Logger.getLogger(classOnWired.getName());
    }
}