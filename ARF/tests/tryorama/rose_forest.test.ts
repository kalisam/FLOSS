import { test } from 'vitest'
import { runScenario, pause, CallableCell } from '@holochain/tryorama'
import { NewEntryAction, ActionHash, Record, AppBundleSource, fakeActionHash, fakeAgentPubKey, fakeEntryHash } from '@holochain/client'
import { dnas, apps } from '../../dnas/rose_forest/dna.yaml'

test('create and search for a rose node', async () => {
  await runScenario(async scenario => {
    // Construct proper paths for your DNAs
    const appSource = { app_bundle_source: { path: './dnas/rose_forest/rose_forest.dna' } }

    // Set up the app to be installed
    const app = { app_source: appSource, installed_app_id: 'rose-forest-app' }

    // Add 2 players with the test app to the Scenario. The returned players
    // can be used to call Zome functions on their respective DNAs.
    const [alice, bob] = await scenario.addPlayersWithApps([app, app])

    // Shortcut to the Zome function interface
    const alice_rose_forest = alice.cells[0] as CallableCell
    const bob_rose_forest = bob.cells[0] as CallableCell

    // 1. Alice creates a RoseNode
    const content = 'This is a test node'
    const embedding = Array.from({ length: 128 }, () => Math.random())
    const license = 'MIT'
    const metadata = { model_id: 'test-model', model_card_hash: 'sha256:12345' }

    const addNodeInput = { content, embedding, license, metadata }
    const nodeHash: ActionHash = await alice_rose_forest.callZome({ zome_name: 'coordinator', fn_name: 'add_knowledge', payload: addNodeInput })
    console.log('Created RoseNode with hash:', nodeHash)

    await pause(1200)

    // 2. Bob searches for the node
    const searchInput = { query_embedding: embedding, k: 1 }
    const searchResults: any[] = await bob_rose_forest.callZome({ zome_name: 'coordinator', fn_name: 'vector_search', payload: searchInput })
    console.log('Search results:', searchResults)

    // 3. Assert that the search result is correct
    test.ok(searchResults.length > 0)
    test.equal(searchResults[0].content, content)
    test.deepEqual(searchResults[0].hash, nodeHash)
  })
})





test('create a thought credential', async () => {
  await runScenario(async scenario => {
    const appSource = { app_bundle_source: { path: './dnas/rose_forest/rose_forest.dna' } }
    const app = { app_source: appSource, installed_app_id: 'rose-forest-app' }
    const [alice] = await scenario.addPlayersWithApps([app])
    const alice_rose_forest = alice.cells[0] as CallableCell

    const content = Array.from({ length: 128 }, () => Math.random());
    const connotation = 1; // Example: positive connotation
    const provenance = alice.agentPubKey;
    const resonance = [alice.agentPubKey];
    const impact = 0.8; // Example: high impact

    const createThoughtCredentialInput = { content, connotation, provenance, resonance, impact };
    const credentialHash: ActionHash = await alice_rose_forest.callZome({ zome_name: 'coordinator', fn_name: 'create_thought_credential', payload: createThoughtCredentialInput });
    console.log('Created ThoughtCredential with hash:', credentialHash);

    test.ok(credentialHash);
  });
});

