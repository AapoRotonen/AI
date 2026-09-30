package com.supportai.service;

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException() { super("The requested resource was not found."); }
}
