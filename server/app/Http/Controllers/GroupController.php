<?php

namespace App\Http\Controllers;

use App\Models\Cube;
use App\Models\GroupOfThree;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class GroupController extends Controller
{
    public function groupCubes()
    {
        $groupCubes = GroupOfThree::with('cubes')
            ->orderBy('created_at', 'desc')
            ->take(5)
            ->get();
        return response()->json($groupCubes);
    }

    public function getGroupById($id)
    {
        $group = GroupOfThree::with('cubes')->find($id);
        if (!$group) {
            return response()->json(['message' => 'Group not found'], 404);
        }
        return response()->json($group);
    }

    public function averageByColor($color)
    {
        $cubes = Cube::where('color', $color)->pluck('individual_time');

        if ($cubes->isEmpty()) {
            return response()->json([
                'color' => $color,
                'average_individual_time' => 0
            ]);
        }

        $sum = $cubes->sum();
        $count = $cubes->count();
        $average = $sum / $count;

        return response()->json([
            'color' => $color,
            'average_individual_time' => $average
        ]);
    }

    public function delayed()
    {
        $groups = GroupOfThree::with('cubes')
            ->orderBy('created_at', 'desc')
            ->get();

        $delayed = [];

        foreach ($groups as $group) {
            if ($group->group_time > 10) {
                $maxCube = $group->cubes->sortByDesc('individual_time')->first();
                $diff = ($group->group_time) - 10;

                $delayed[] = [
                    'type' => 'high_time',
                    'message' => 'Grupo com tempo acima do esperado.',
                    'group_id' => $group->id,
                    'group_time' => $group->group_time,
                    'cube' => [
                        'id' => $maxCube->id,
                        'color' => $maxCube->color,
                        'face' => $maxCube->face,
                        'individual_time' => $maxCube->individual_time,
                        'diff' => $diff
                    ]
                ];
            }
        }

        return response()->json($delayed);
    }

    public function early(){
        $groups = GroupOfThree::with('cubes')
            ->orderBy('created_at', 'desc')
            ->get();

        $early = [];

        foreach ($groups as $group) {
            if ($group->group_time < 2) {
                $minCube = $group->cubes->sortBy('individual_time')->first();
                $diff = 2 - $group->group_time;

                $early[] = [
                    'type' => 'low_time',
                    'message' => 'Grupo com tempo abaixo do esperado.',
                    'group_id' => $group->id,
                    'group_time' => $group->group_time,
                    'cube' => [
                        'id' => $minCube->id,
                        'color' => $minCube->color,
                        'face' => $minCube->face,
                        'individual_time' => $minCube->individual_time,
                        'diff' => $diff
                    ]
                ];
            }
        }

        return response()->json($early);
    }

    public function notifications()
    {
        $delayed = $this->Delayed()->getData();
        $early = $this->early()->getData();

        $allNotifications = array_merge($delayed, $early);

        usort($allNotifications, function ($a, $b) {
            return $b->group_id <=> $a->group_id;
        });

        return response()->json($allNotifications);
    }

    public function latestGroupTimes(){
        $groupTimes = GroupOfThree::orderBy('created_at', 'desc')
            ->take(7)
            ->get(['id', 'group_time']);

        return response()->json($groupTimes);
    }

    public function store(Request $request)
    {
        $request->validate([
            'group_time' => 'required|numeric',
            'cubes' => 'required|array|size:3',
            'cubes.*.color' => 'required|string',
            'cubes.*.face' => 'required|string',
            'cubes.*.individual_time' => 'required|numeric',
        ]);

        try {
            // cria o grupo sem os cubos ainda
            $group = GroupOfThree::create([
                'group_time' => $request->group_time
            ]); 

            $cube_ids = [];

            // cria os cubos e associa ao grupo
            foreach ($request->cubes as $cubeData) {
                $cube = Cube::create([
                    'group_id' => $group->id,
                    'color' => $cubeData['color'],
                    'face' => $cubeData['face'],
                    'individual_time' => $cubeData['individual_time']
                ]);
                $cube_ids[] = $cube->id;
            }

            // atualiza o grupo com os ids dos cubos
            $group->update([
                'cube_1' => $cube_ids[0],
                'cube_2' => $cube_ids[1],
                'cube_3' => $cube_ids[2]
            ]);

            // retorna o grupo com os cubos carregados
            return response()->json($group->load('cubes'), 201);
        } catch (\Throwable $e) {
            return response()->json([
                'message' => 'Ocorreu um erro ao processar sua requisição.'
            ], 500);
        }
    }
}
