<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\GroupController;

Route::get('/groups', [GroupController::class, 'groupCubes']);
Route::post('/groups', [GroupController::class, 'store']);
Route::get('/average/{color}', [GroupController::class, 'AverageByColor']);