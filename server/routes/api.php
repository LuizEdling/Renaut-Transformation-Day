<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\GroupController;

Route::get('/groups', [GroupController::class, 'groupCubes']);
Route::post('/groups', [GroupController::class, 'store']);
Route::get('/average/{color}', [GroupController::class, 'averageByColor']);
Route::get('/notifications/delayed', [GroupController::class, 'delayed']);
Route::get('/notifications/early', [GroupController::class, 'early']);
Route::get('/notifications', [GroupController::class, 'notifications']);
Route::get('/latest-group-times', [GroupController::class, 'latestGroupTimes']);