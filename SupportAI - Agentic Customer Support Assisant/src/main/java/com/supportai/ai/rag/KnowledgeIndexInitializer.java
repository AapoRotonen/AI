package com.supportai.ai.rag;

import org.springframework.ai.document.Document;
import com.supportai.ai.AiAvailability;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Component
public class KnowledgeIndexInitializer implements ApplicationRunner {
    private static final Logger log = LoggerFactory.getLogger(KnowledgeIndexInitializer.class);
    private final KnowledgeCorpus corpus;
    private final ObjectProvider<VectorStore> vectorStores;
    private final JdbcTemplate jdbc;
    private final AiAvailability aiAvailability;

    public KnowledgeIndexInitializer(KnowledgeCorpus corpus, ObjectProvider<VectorStore> vectorStores, JdbcTemplate jdbc,
                                     AiAvailability aiAvailability) {
        this.corpus = corpus;
        this.vectorStores = vectorStores;
        this.jdbc = jdbc;
        this.aiAvailability = aiAvailability;
    }

    @Override
    public void run(ApplicationArguments args) throws Exception {
        if (!aiAvailability.enabled() || corpus.chunks().isEmpty()) return;
        try {
            VectorStore vectorStore = vectorStores.getIfAvailable();
            if (vectorStore == null) return;
            Map<String, List<KnowledgeChunk>> bySource = corpus.chunks().stream().collect(java.util.stream.Collectors.groupingBy(
                    KnowledgeChunk::source, java.util.LinkedHashMap::new, java.util.stream.Collectors.toList()));
            for (var entry : bySource.entrySet()) {
                String source = entry.getKey();
                List<KnowledgeChunk> chunks = entry.getValue();
                String hash = sha256(chunks.stream().map(c -> c.source() + "|" + c.title() + "|" + c.category() + "|" + c.text())
                        .reduce("", (a, b) -> a + "\n" + b));
                var existing = jdbc.query("SELECT content_hash, chunk_count FROM supportai_kb_ingestion WHERE document_key = ?",
                        rs -> rs.next() ? new Existing(rs.getString(1), rs.getInt(2)) : null, source);
                if (existing != null && existing.hash().equals(hash)) continue;
                if (existing != null) {
                    List<String> oldIds = java.util.stream.IntStream.range(0, existing.count())
                            .mapToObj(index -> documentId(source, index)).toList();
                    vectorStore.delete(oldIds);
                }
                List<Document> documents = chunks.stream().map(chunk -> new Document(documentId(source, chunk.index()), chunk.text(),
                        Map.of("documentId", source, "title", chunk.title(), "category", chunk.category(), "source", chunk.source(),
                                "chunk", chunk.index(), "version", "1"))).toList();
                vectorStore.add(documents);
                jdbc.update("INSERT INTO supportai_kb_ingestion(document_key, content_hash, chunk_count) VALUES (?, ?, ?) " +
                        "ON CONFLICT(document_key) DO UPDATE SET content_hash = EXCLUDED.content_hash, chunk_count = EXCLUDED.chunk_count, ingested_at = CURRENT_TIMESTAMP",
                        source, hash, chunks.size());
            }
        } catch (Exception failure) {
            log.warn("Knowledge vector indexing could not complete; local keyword retrieval remains available.");
        }
    }

    static String documentId(String source, int index) {
        return UUID.nameUUIDFromBytes((source + ":" + index).getBytes(StandardCharsets.UTF_8)).toString();
    }

    private String sha256(String text) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8)));
    }

    private record Existing(String hash, int count) { }
}
