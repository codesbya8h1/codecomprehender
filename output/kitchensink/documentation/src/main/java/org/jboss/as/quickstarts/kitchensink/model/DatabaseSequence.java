package org.jboss.as.quickstarts.kitchensink.model;

// Importing necessary Spring Data annotations for MongoDB document mapping
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

// Importing BigInteger class for handling large integer values
import java.math.BigInteger;

/**
 * The DatabaseSequence class represents a sequence generator for database entries.
 * It is mapped to a MongoDB collection named "database_sequences".
 * 
 * This class is designed to hold a unique identifier and a corresponding sequence value,
 * which can be used for generating unique keys or identifiers in the application.
 * 
 * Design Patterns: This class follows the Data Transfer Object (DTO) pattern, 
 * encapsulating the data to be transferred between the application and the database.
 * 
 * Author: [Your Name]
 * Version: 1.0
 * Since: 2023-10-01
 * 
 * Related Classes: This class is related to other classes that require unique sequence generation.
 * 
 * Usage Example:
 * DatabaseSequence sequence = new DatabaseSequence();
 * sequence.setId("mySequence");
 * sequence.setSequence(BigInteger.valueOf(1));
 * 
 * Thread Safety: This class is not thread-safe. If used in a multi-threaded environment,
 * external synchronization mechanisms should be implemented.
 */
@Document(collection = "database_sequences") // Specifies the MongoDB collection name
public class DatabaseSequence {
    
    @Id // Marks this field as the identifier for the document in MongoDB
    private String id; // Unique identifier for the sequence

    private BigInteger sequence; // The current sequence value

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
     *           Must not be null or empty.
     */
    public void setId(String id) {
        this.id = id; // Assigns the provided id to the id field
    }

    /**
     * Retrieves the current sequence value.
     * 
     * @return BigInteger representing the current sequence value.
     */
    public BigInteger getSequence() {
        return sequence; // Returns the sequence field
    }

    /**
     * Sets the current sequence value.
     * 
     * @param sequence BigInteger representing the sequence value to set.
     *                 Must not be null and should be a non-negative value.
     */
    public void setSequence(BigInteger sequence) {
        this.sequence = sequence; // Assigns the provided sequence to the sequence field
    }
}