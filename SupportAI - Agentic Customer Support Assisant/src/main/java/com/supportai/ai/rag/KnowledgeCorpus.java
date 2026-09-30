package com.supportai.ai.rag;

import org.springframework.core.io.Resource;
import org.springframework.core.io.support.ResourcePatternResolver;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

@Component
public class KnowledgeCorpus {
    private static final int MAX_CHUNK_CHARS = 1100;
    private final List<KnowledgeChunk> chunks;

    public KnowledgeCorpus(ResourcePatternResolver resources) throws IOException {
        List<KnowledgeChunk> loaded = new ArrayList<>();
        for (Resource resource : resources.getResources("classpath*:knowledge/*.md")) {
            if (!resource.exists()) continue;
            String source = resource.getFilename() == null ? "knowledge.md" : resource.getFilename();
            String content;
            try (var input = resource.getInputStream()) {
                content = new String(input.readAllBytes(), StandardCharsets.UTF_8).trim();
            }
            String title = content.lines().filter(line -> line.startsWith("# ")).findFirst()
                    .map(line -> line.substring(2).trim()).orElse(source.replace('-', ' '));
            String category = content.lines().filter(line -> line.toLowerCase().startsWith("category:"))
                    .findFirst().map(line -> line.substring("category:".length()).trim())
                    .orElseGet(() -> source.contains("-") ? source.substring(0, source.indexOf('-')) : "general");
            List<String> pieces = split(content);
            for (int i = 0; i < pieces.size(); i++) {
                loaded.add(new KnowledgeChunk(source + ":" + i, title, category, source, pieces.get(i), i));
            }
        }
        this.chunks = List.copyOf(loaded);
    }

    public List<KnowledgeChunk> chunks() { return chunks; }

    private List<String> split(String content) {
        List<String> result = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        for (String paragraph : content.split("\\R\\s*\\R")) {
            String part = paragraph.trim();
            if (part.isEmpty()) continue;
            if (current.length() > 0 && current.length() + part.length() + 2 > MAX_CHUNK_CHARS) {
                result.add(current.toString());
                current.setLength(0);
            }
            if (part.length() > MAX_CHUNK_CHARS) {
                for (int start = 0; start < part.length(); start += MAX_CHUNK_CHARS) {
                    String slice = part.substring(start, Math.min(start + MAX_CHUNK_CHARS, part.length()));
                    if (current.length() > 0) { result.add(current.toString()); current.setLength(0); }
                    result.add(slice);
                }
            } else {
                if (current.length() > 0) current.append("\n\n");
                current.append(part);
            }
        }
        if (current.length() > 0) result.add(current.toString());
        return result;
    }
}
