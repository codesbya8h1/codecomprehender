package org.jboss.as.quickstarts.kitchensink.model;

// Importing necessary Spring Data annotations for MongoDB
import org.springframework.data.annotation.Id; // Annotation to indicate the field is the document ID
import org.springframework.data.mongodb.core.mapping.Document; // Annotation to indicate the class is a MongoDB document

import java.math.BigInteger; // Importing BigInteger class for handling large integers

/**
 * The DatabaseSequence class represents a sequence generator for database entries.
 * It is mapped to a MongoDB collection named "database_sequences".
 * 
 * This class is designed to hold a unique identifier and a corresponding sequence value,
 * which can be used for generating unique keys or identifiers in the application.
 * 
 * Design Patterns: This class follows the Data Transfer Object (DTO) pattern, 
 * encapsulating the data to be transferred between layers of the application.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023-10-01
 * 
 * Related Classes: This class may be used in conjunction with other classes that require 
 * unique sequence generation, such as entity classes that need unique identifiers.
 * 
 * Usage Example:
 * DatabaseSequence sequence = new DatabaseSequence();
 * sequence.setId("user_sequence");
 * sequence.setSequence(BigInteger.valueOf(1));
 * 
 * Thread Safety: This class is not thread-safe. If used in a multi-threaded environment, 
 * external synchronization mechanisms should be implemented to ensure thread safety.
 */
@Document(collection = "database_sequences") // Specifies the MongoDB collection name
public class DatabaseSequence {
    
    @Id // Marks this field as the unique identifier for the MongoDB document
    private String id; // Unique identifier for the sequence

    private BigInteger sequence; // The current value of the sequence

    /**
     * Retrieves the unique identifier of the sequence.
     * 
     * @return String representing the unique identifier of the sequence.
     */
    public String getId() {
        return id; // Returns the id field
    }

    /**
     * Sets the unique identifier for the sequence.
     * 
     * @param id String representing the unique identifier to set.
     */
    public void setId(String id) {
        this.id = id; // Assigns the provided id to the id field
    }

    /**
     * Retrieves the current value of the sequence.
     * 
     * @return BigInteger representing the current sequence value.
     */
    public BigInteger getSequence() {
        return sequence; // Returns the sequence field
    }

    /**
     * Sets the current value of the sequence.
     * 
     * @param sequence BigInteger representing the new sequence value to set.
     */
    public void setSequence(BigInteger sequence) {
        this.sequence = sequence; // Assigns the provided sequence value to the sequence field
    }
}