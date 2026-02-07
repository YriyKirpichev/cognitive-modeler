import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.cognitive_map_dependencies import get_cognitive_map_store
from app.models.cognitive_map_models import (
    ScenarioModel,
    ScenarioParams,
    ScenarioResult,
)
from app.storage.cognitive_map_store import CognitiveMapStore
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

logger = logging.getLogger("app")


@router.get("/", response_model=list[ScenarioModel])
async def get_scenarios(store: CognitiveMapStore = Depends(get_cognitive_map_store)):
    """Get all scenarios."""
    cognitive_map = await store.get()
    return cognitive_map.fcm.scenarios


@router.get("/{scenario_id}", response_model=ScenarioModel)
async def get_scenario(
    scenario_id: str,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    """Get a specific scenario by ID."""
    cognitive_map = await store.get()

    for scenario in cognitive_map.fcm.scenarios:
        if scenario.id == scenario_id:
            return scenario

    raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")


@router.post("/", response_model=ScenarioModel)
async def create_scenario(
    params: ScenarioParams,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    """Create a new scenario."""
    try:
        cognitive_map = await store.get()

        # Generate unique ID
        scenario_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        # Create new scenario
        new_scenario = ScenarioModel(
            id=scenario_id,
            params=params,
            result=None,
            created_at=now,
            updated_at=now,
        )

        # Add to cognitive map
        cognitive_map.fcm.scenarios.append(new_scenario)

        # Save
        await store.put(cognitive_map)

        logger.info(f"Created scenario: {scenario_id} - {params.name}")

        return new_scenario
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{scenario_id}", response_model=ScenarioModel)
async def update_scenario(
    scenario_id: str,
    params: ScenarioParams,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    """Update scenario parameters."""
    try:
        cognitive_map = await store.get()

        # Find scenario
        scenario_index = None
        for idx, scenario in enumerate(cognitive_map.fcm.scenarios):
            if scenario.id == scenario_id:
                scenario_index = idx
                break

        if scenario_index is None:
            raise HTTPException(
                status_code=404, detail=f"Scenario '{scenario_id}' not found"
            )

        # Update scenario
        scenario = cognitive_map.fcm.scenarios[scenario_index]
        scenario.params = params
        scenario.updated_at = datetime.utcnow().isoformat() + "Z"

        # Save
        await store.put(cognitive_map)

        logger.info(f"Updated scenario: {scenario_id}")

        return scenario
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    """Delete a scenario."""
    try:
        cognitive_map = await store.get()

        # Find and remove scenario
        scenario_index = None
        for idx, scenario in enumerate(cognitive_map.fcm.scenarios):
            if scenario.id == scenario_id:
                scenario_index = idx
                break

        if scenario_index is None:
            raise HTTPException(
                status_code=404, detail=f"Scenario '{scenario_id}' not found"
            )

        cognitive_map.fcm.scenarios.pop(scenario_index)

        # Save
        await store.put(cognitive_map)

        logger.info(f"Deleted scenario: {scenario_id}")

        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{scenario_id}/run", response_model=ScenarioResult)
async def run_scenario(
    scenario_id: str,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    """Run simulation for a scenario."""
    try:
        cognitive_map = await store.get()

        # Find scenario
        scenario_index = None
        for idx, scenario in enumerate(cognitive_map.fcm.scenarios):
            if scenario.id == scenario_id:
                scenario_index = idx
                break

        if scenario_index is None:
            raise HTTPException(
                status_code=404, detail=f"Scenario '{scenario_id}' not found"
            )

        scenario = cognitive_map.fcm.scenarios[scenario_index]

        # Run simulation
        logger.info(f"Running simulation for scenario: {scenario_id}")
        result = ScenarioService.run_simulation(cognitive_map, scenario.params)

        # Update scenario with result
        scenario.result = result
        scenario.updated_at = datetime.utcnow().isoformat() + "Z"

        # Save
        await store.put(cognitive_map)

        logger.info(
            f"Simulation completed for scenario: {scenario_id}, "
            f"iterations={result.iterations_count}, converged={result.converged}"
        )

        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run scenario simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
