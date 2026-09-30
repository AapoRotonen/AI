package com.supportai.ai.rag;

import com.supportai.api.ApiDtos.KnowledgeSource;
import com.supportai.api.ApiDtos.KnowledgeToolResult;
import com.supportai.ai.AiAvailability;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
public class KnowledgeService {
    private static final Pattern WORDS = Pattern.compile("[a-z0-9]{3,}");
    private final KnowledgeCorpus corpus;
    private final ObjectProvider<VectorStore> vectorStores;
    private final AiAvailability aiAvailability;

    public KnowledgeService(KnowledgeCorpus corpus, ObjectProvider<VectorStore> vectorStores, AiAvailability aiAvailability) {
        this.corpus = corpus;
        this.vectorStores = vectorStores;
        this.aiAvailability = aiAvailability;
    }

    public KnowledgeToolResult search(String query) {
        if (query == null || query.isBlank() || query.length() > 500) {
            throw new IllegalArgumentException("A knowledge query of 1 to 500 characters is required.");
        }
        List<KnowledgeChunk> matches = new ArrayList<>();
        if (aiAvailability.enabled()) {
            try {
                VectorStore vectorStore = vectorStores.getIfAvailable();
                if (vectorStore != null) {
                    matches = vectorStore.similaritySearch(SearchRequest.builder().query(query).topK(4).similarityThreshold(0.52).build())
                            .stream().map(this::toChunk).toList();
                }
            } catch (RuntimeException ignored) {
                // Keep policy lookup available from the checked-in corpus if embeddings or pgvector are unavailable.
            }
        }
        if (matches.isEmpty()) matches = lexicalSearch(query);
        if (matches.isEmpty()) return new KnowledgeToolResult("No relevant internal policy was found. Do not infer a company policy from general knowledge.", List.of());
        List<KnowledgeSource> sources = matches.stream().map(c -> new KnowledgeSource(c.source(), c.title(), c.category())).distinct().toList();
        String evidence = matches.stream().map(c -> "[Source: " + c.title() + " | " + c.source() + "]\n" + c.text())
                .collect(Collectors.joining("\n\n---\n\n"));
        return new KnowledgeToolResult(evidence, sources);
    }

    private KnowledgeChunk toChunk(Document document) {
        Map<String, Object> metadata = document.getMetadata();
        return new KnowledgeChunk(document.getId(), String.valueOf(metadata.getOrDefault("title", "Support policy")),
                String.valueOf(metadata.getOrDefault("category", "general")),
                String.valueOf(metadata.getOrDefault("source", "knowledge base")), document.getText(), 0);
    }

    private List<KnowledgeChunk> lexicalSearch(String query) {
        Set<String> queryWords = words(query);
        if (queryWords.isEmpty()) return List.of();
        return corpus.chunks().stream().map(chunk -> Map.entry(chunk, score(queryWords, words(chunk.text() + " " + chunk.title()))))
                .filter(entry -> entry.getValue() > 0)
                .sorted(Map.Entry.<KnowledgeChunk, Integer>comparingByValue().reversed())
                .limit(4).map(Map.Entry::getKey).toList();
    }

    private Set<String> words(String value) {
        Set<String> result = new HashSet<>();
        var matcher = WORDS.matcher(value.toLowerCase(Locale.ROOT));
        while (matcher.find()) result.add(matcher.group());
        return result;
    }

    private int score(Set<String> query, Set<String> content) {
        return (int) query.stream().filter(content::contains).count();
    }
}
