targetScope = 'resourceGroup'

@description('Azure region shared by the app, database, and storage. Use a region supported for all services, for example Sweden Central.')
param location string = resourceGroup().location

@description('A globally unique 6-10 character lowercase letter/number suffix, for example k7p4m2x9.')
@minLength(6)
@maxLength(10)
param suffix string

@description('Name of the versioned Chroma ZIP to restore from the private Blob container.')
param ragIndexBlobName string = 'index-placeholder.zip'

var appName = 'koivu-${suffix}'
var environmentName = 'cae-koivu-${suffix}'
var identityName = 'id-koivu-${suffix}'
var registryName = 'koivu${suffix}'
var storageName = 'koivu${suffix}'
var cosmosName = 'koivu-cosmos-${suffix}'
var workspaceName = 'log-koivu-${suffix}'
var databaseName = 'koivu'
var ragContainerName = 'koivu-rag'

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {}
}

resource ragContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: ragContainerName
  properties: {
    publicAccess: 'None'
  }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    enableAutomaticFailover: false
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmos
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

resource users 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDatabase
  name: 'users'
  properties: {
    resource: {
      id: 'users'
      partitionKey: {
        paths: [ '/email' ]
        kind: 'Hash'
        version: 2
      }
    }
  }
}

resource sessions 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDatabase
  name: 'sessions'
  properties: {
    resource: {
      id: 'sessions'
      defaultTtl: -1
      partitionKey: {
        paths: [ '/token_hash' ]
        kind: 'Hash'
        version: 2
      }
    }
  }
}

resource orders 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDatabase
  name: 'orders'
  properties: {
    resource: {
      id: 'orders'
      partitionKey: {
        paths: [ '/user_id' ]
        kind: 'Hash'
        version: 2
      }
    }
  }
}

resource supportCases 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDatabase
  name: 'support_cases'
  properties: {
    resource: {
      id: 'support_cases'
      partitionKey: {
        paths: [ '/user_id' ]
        kind: 'Hash'
        version: 2
      }
    }
  }
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        // Keep the bootstrap sample private; the application workflow publishes the real app.
        external: false
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: appIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'koivu-store'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: 1.0
            memory: '2Gi'
          }
          env: [
            { name: 'APP_ENVIRONMENT', value: 'local' }
            { name: 'DATABASE_BACKEND', value: 'sqlite' }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
  dependsOn: [
    ragContainer
    cosmosDatabase
    users
    sessions
    orders
    supportCases
  ]
}

output containerAppName string = app.name
output containerAppUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
output containerRegistryName string = registry.name
output containerRegistryLoginServer string = registry.properties.loginServer
output appIdentityName string = appIdentity.name
output appIdentityPrincipalId string = appIdentity.properties.principalId
output appIdentityClientId string = appIdentity.properties.clientId
output cosmosAccountName string = cosmos.name
output cosmosEndpoint string = cosmos.properties.documentEndpoint
output cosmosDatabaseName string = cosmosDatabase.name
output storageAccountName string = storage.name
output ragContainerName string = ragContainer.name
output expectedInitialRagBlobName string = ragIndexBlobName
output logAnalyticsWorkspaceName string = workspace.name

