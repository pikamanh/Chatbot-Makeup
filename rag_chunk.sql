CREATE TABLE rag_chunks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    embedding JSON  -- lưu embedding dưới dạng JSON string
);
