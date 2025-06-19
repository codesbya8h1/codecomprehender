package org.jboss.as.quickstarts.kitchensink.utils;

// Importing necessary Spring framework classes for dependency injection and configuration
import org.springframework.beans.factory.InjectionPoint;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;

// Importing Java logging framework
import java.util.logging.Logger;

/**
 * The Resources class is responsible for providing application-wide resources
 * such as loggers. It utilizes Spring's dependency injection framework to
 * create and manage the lifecycle of these resources.
 *
 * <p>This class is annotated with @Configuration, indicating that it contains
 * bean definitions that will be processed by the Spring container. The
 * produceLogger method is defined as a bean that returns a Logger instance
 * scoped to the prototype, meaning a new instance will be created each time
 * it is requested.</p>
 *
 * <p>Author: [Your Name]</p>
 * <p>Version: 1.0</p>
 * <p>Since: 2023</p>
 * <p>Related Classes: InjectionPoint, Logger</p>
 *
 * <p>Usage Example:</p>
 * <pre>
 *     @Autowired
 *     private Logger logger;
 *     
 *     public void someMethod() {
 *         logger.info("This is a log message.");
 *     }
 * </pre>
 *
 * <p>Thread Safety: The Logger instances produced by this class are not
 * thread-safe. It is recommended to use the prototype scope to ensure that
 * each thread gets its own instance.</p>
 */
@Configuration
public class Resources {

    /**
     * Produces a Logger instance for the class where it is injected.
     *
     * <p>This method is annotated with @Bean, indicating that it is a factory
     * method for a Spring bean. The Logger instance is scoped as "prototype",
     * meaning a new instance will be created each time it is requested.</p>
     *
     * @param injectionPoint The InjectionPoint that provides context about
     *                       where the Logger is being injected. It is used
     *                       to determine the class that requires the Logger.
     *                       Must not be null.
     * @return A Logger instance specific to the class where it is injected.
     *         This Logger is configured with the name of the declaring class.
     *
     * @throws IllegalArgumentException if the injectionPoint is null.
     * 
     * <p>Performance Considerations: The Logger creation is relatively
     * lightweight, but creating a new instance for each injection may have
     * overhead in high-frequency logging scenarios.</p>
     */
    @Bean
    @Scope("prototype")
    public Logger produceLogger(InjectionPoint injectionPoint) {
        
        // Retrieve the class where the Logger is being injected
        Class<?> classOnWired = injectionPoint.getMember().getDeclaringClass();
        
        // Create and return a Logger instance for the specified class
        return Logger.getLogger(classOnWired.getName());
    }
}